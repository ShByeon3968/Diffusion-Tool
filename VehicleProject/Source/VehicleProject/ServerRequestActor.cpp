// Fill out your copyright notice in the Description page of Project Settings.


#include "ServerRequestActor.h"
#include "Interfaces/IHttpResponse.h"
#include "Interfaces/IHttpRequest.h"
#include "Misc/Paths.h"
#include "Misc/FileHelper.h"
#include "ImageUtils.h"
#include "IImageWrapper.h"
#include "IImageWrapperModule.h"
#include "Logging/LogMacros.h"
#include "Modules/ModuleManager.h"
#include "TimerManager.h"
#include "Engine/World.h"
#include "Misc/FileHelper.h"

// Sets default values
AServerRequestActor::AServerRequestActor()
{
 	// Set this actor to call Tick() every frame.  You can turn this off to improve performance if you don't need it.
	PrimaryActorTick.bCanEverTick = false;

}

// Called when the game starts or when spawned
void AServerRequestActor::BeginPlay()
{
	Super::BeginPlay();
	
}

// Called every frame
void AServerRequestActor::Tick(float DeltaTime)
{
	Super::Tick(DeltaTime);

}

void AServerRequestActor::RequestMeshGeneration(const FString& Prompt, const FString& Model, FOnMeshGeneratedDynamic Callback)
{
    TSharedRef<IHttpRequest, ESPMode::ThreadSafe> Request = FHttpModule::Get().CreateRequest();
    Request->SetURL(TEXT("http://localhost:8000/generate/"));
    Request->SetVerb("POST");
    Request->SetHeader(TEXT("Content-Type"), TEXT("application/x-www-form-urlencoded"));

    FString Body = FString::Printf(TEXT("prompt=%s&model=%s"),
        *FGenericPlatformHttp::UrlEncode(Prompt),
        *FGenericPlatformHttp::UrlEncode(Model));
    Request->SetContentAsString(Body);

    // Callback 캡처를 위한 람다 사용
    Request->OnProcessRequestComplete().BindLambda(
        [this, Callback](FHttpRequestPtr Req, FHttpResponsePtr Res, bool bSuccess)
        {
            this->OnMeshGenerationResponse(Req, Res, bSuccess, Callback);
        });

    Request->ProcessRequest();
}

void AServerRequestActor::OnMeshGenerationResponse(FHttpRequestPtr Request, FHttpResponsePtr Response, bool bWasSuccessful, FOnMeshGeneratedDynamic Callback)
{
    if (!bWasSuccessful || !Response.IsValid())
    {
        UE_LOG(LogTemp, Error, TEXT("[HTTP] request failed"));
        return;
    }

    if (Response->GetResponseCode() != 200)
    {
        UE_LOG(LogTemp, Error, TEXT("[HTTP] response failed: %s"), *Response->GetContentAsString());
        return;
    }

    FString ResponseContent = Response->GetContentAsString();
    TSharedPtr<FJsonObject> JsonObject;
    TSharedRef<TJsonReader<>> Reader = TJsonReaderFactory<>::Create(ResponseContent);

    if (FJsonSerializer::Deserialize(Reader, JsonObject) && JsonObject.IsValid())
    {
        FString UID = JsonObject->GetStringField("uid");

        UE_LOG(LogTemp, Log, TEXT("[MeshGen] UID received: %s"), *UID);

        if (Callback.IsBound())
        {
            Callback.Execute(UID);
        }
    }
    else
    {
        UE_LOG(LogTemp, Error, TEXT("[HTTP] JSON parsing failed"));
    }
}


UTexture2D* AServerRequestActor::LoadTextureFromFile(const FString& FilePath)
{
    TArray<uint8> RawFileData;
    if (!FFileHelper::LoadFileToArray(RawFileData, *FilePath))
    {
        UE_LOG(LogTemp, Error, TEXT("[Image] Failed to read file: %s"), *FilePath);
        return nullptr;
    }

    IImageWrapperModule& ImageWrapperModule = FModuleManager::LoadModuleChecked<IImageWrapperModule>(FName("ImageWrapper"));
    TSharedPtr<IImageWrapper> ImageWrapper = ImageWrapperModule.CreateImageWrapper(EImageFormat::PNG);

    if (ImageWrapper.IsValid() && ImageWrapper->SetCompressed(RawFileData.GetData(), RawFileData.Num()))
    {
        TArray64<uint8> UncompressedBGRA;
        if (ImageWrapper->GetRaw(ERGBFormat::BGRA, 8, UncompressedBGRA))
        {
            UTexture2D* Texture = UTexture2D::CreateTransient(
                ImageWrapper->GetWidth(),
                ImageWrapper->GetHeight(),
                PF_B8G8R8A8
            );

            if (!Texture) return nullptr;

            void* TextureData = Texture->GetPlatformData()->Mips[0].BulkData.Lock(LOCK_READ_WRITE);
            FMemory::Memcpy(TextureData, UncompressedBGRA.GetData(), UncompressedBGRA.Num());
            Texture->GetPlatformData()->Mips[0].BulkData.Unlock();

            Texture->UpdateResource();
            return Texture;
        }
    }

    UE_LOG(LogTemp, Error, TEXT("[Image] Failed to decode image: %s"), *FilePath);
    return nullptr;
}

// 이미지 요청 및 응답 처리

void AServerRequestActor::OnImageResponseReceived(FHttpRequestPtr Request, FHttpResponsePtr Response, bool bWasSuccessful, FOnImageDownloaded Callback, FString UID, FString Type)
{
    if (!bWasSuccessful || !Response.IsValid() || Response->GetResponseCode() != 200)
    {
        UE_LOG(LogTemp, Error, TEXT("[Image] HTTP request failed or invalid response."));
        Callback.ExecuteIfBound(TEXT(""), false);
        return;
    }

    const TArray<uint8>& ImageData = Response->GetContent();

    FString SaveDir = FPaths::ProjectSavedDir() + "/DownloadedImages/" + UID + "/";
    FString Filename = Type + "_image.png";
    FString FullPath = SaveDir + Filename;

    IPlatformFile& PlatformFile = FPlatformFileManager::Get().GetPlatformFile();
    if (!PlatformFile.DirectoryExists(*SaveDir))
    {
        PlatformFile.CreateDirectoryTree(*SaveDir);
    }

    if (FFileHelper::SaveArrayToFile(ImageData, *FullPath))
    {
        UE_LOG(LogTemp, Log, TEXT("[Image] Saved to %s"), *FullPath);

        UTexture2D* LoadedTexture = LoadTextureFromFile(FullPath);
        if (LoadedTexture)
        {
            Callback.ExecuteIfBound(FullPath, true);
        }
        else
        {
            Callback.ExecuteIfBound(TEXT(""), false);
        }
    }
    else
    {
        UE_LOG(LogTemp, Error, TEXT("[Image] Failed to save image."));
        Callback.ExecuteIfBound(TEXT(""), false);
    }
}


void AServerRequestActor::RequestImageFromServer(const FString& UID, const FString& Type, const FOnImageDownloaded& Callback)
{
    if (!(Type == "gen" || Type == "mvs"))
    {
        UE_LOG(LogTemp, Error, TEXT("[Image] Invalid type: %s"), *Type);
        Callback.ExecuteIfBound(TEXT(""), false);
        return;
    }

    FString URL = FString::Printf(TEXT("http://localhost:8000/image/%s/%s"), *UID, *Type);

    TSharedRef<IHttpRequest, ESPMode::ThreadSafe> Request = FHttpModule::Get().CreateRequest();
    Request->SetURL(URL);
    Request->SetVerb("GET");
    Request->SetHeader(TEXT("Content-Type"), TEXT("application/json"));

    Request->OnProcessRequestComplete().BindUObject(this, &AServerRequestActor::OnImageResponseReceived, Callback, UID, Type);
    Request->ProcessRequest();
}

// MeshEdit
void AServerRequestActor::RequestMeshImprovement(const FString& FeedBack, FOnMeshEditedDynamic Callback)
{
    TSharedRef<IHttpRequest, ESPMode::ThreadSafe> Request = FHttpModule::Get().CreateRequest();
    Request->SetURL(TEXT("http://localhost:8000/feedback_rewrite"));
    Request->SetVerb("POST");
    Request->SetHeader(TEXT("Content-Type"), TEXT("application/x-www-form-urlencoded"));

    FString Body = FString::Printf(TEXT("feedback=%s"),
        *FGenericPlatformHttp::UrlEncode(FeedBack));
    Request->SetContentAsString(Body);

    // Callback 캡처를 위한 람다 사용
    Request->OnProcessRequestComplete().BindLambda(
        [this, Callback](FHttpRequestPtr Req, FHttpResponsePtr Res, bool bSuccess)
        {
            this->OnMeshImprovementResponse(Req, Res, bSuccess, Callback);
        });

    Request->ProcessRequest();
}

void AServerRequestActor::OnMeshImprovementResponse(FHttpRequestPtr Request, FHttpResponsePtr Response, bool bWasSuccessful, FOnMeshEditedDynamic Callback)
{
    if (!bWasSuccessful || !Response.IsValid())
    {
        UE_LOG(LogTemp, Error, TEXT("[HTTP] request failed"));
        return;
    }

    if (Response->GetResponseCode() != 200)
    {
        UE_LOG(LogTemp, Error, TEXT("[HTTP] response failed: %s"), *Response->GetContentAsString());
        return;
    }

    FString ResponseContent = Response->GetContentAsString();
    TSharedPtr<FJsonObject> JsonObject;
    TSharedRef<TJsonReader<>> Reader = TJsonReaderFactory<>::Create(ResponseContent);

    if (FJsonSerializer::Deserialize(Reader, JsonObject) && JsonObject.IsValid())
    {
        FString UID = JsonObject->GetStringField("uid");

        UE_LOG(LogTemp, Log, TEXT("[MeshEdited] UID received: %s"), *UID);

        if (Callback.IsBound())
        {
            Callback.Execute(UID);
        }
    }
    else
    {
        UE_LOG(LogTemp, Error, TEXT("[HTTP] JSON parsing failed"));
    }
}
