// Fill out your copyright notice in the Description page of Project Settings.


#include "ServerResponseActor.h"
#include "HttpModule.h"
#include "Interfaces/IHttpResponse.h"

// Sets default values
AServerResponseActor::AServerResponseActor()
{
 	// Set this actor to call Tick() every frame.  You can turn this off to improve performance if you don't need it.
	PrimaryActorTick.bCanEverTick = false;

}

// Called when the game starts or when spawned
void AServerResponseActor::BeginPlay()
{
	Super::BeginPlay();
	
}

// Called every frame
void AServerResponseActor::Tick(float DeltaTime)
{
	Super::Tick(DeltaTime);

}

void AServerResponseActor::GetLastUIDFromServer(const FOnUidReceived& OnSuccess)
{
    TSharedRef<IHttpRequest, ESPMode::ThreadSafe> Request = FHttpModule::Get().CreateRequest();

    // 요청 완료 시 실행될 콜백 바인딩
    Request->OnProcessRequestComplete().BindUObject(this, &AServerResponseActor::OnLastUIDResponse, OnSuccess);

    Request->SetURL(TEXT("http://localhost:8000/last_uid/"));
    Request->SetVerb(TEXT("GET"));
    Request->SetHeader(TEXT("Content-Type"), TEXT("application/json"));
    Request->ProcessRequest();
}

void AServerResponseActor::OnLastUIDResponse(FHttpRequestPtr Request, FHttpResponsePtr Response, bool bWasSuccessful, FOnUidReceived Callback)
{
    if (!bWasSuccessful || !Response.IsValid())
    {
        UE_LOG(LogTemp, Error, TEXT("[UID] HTTP request failed."));
        Callback.ExecuteIfBound(TEXT("none"));
        return;
    }

    UID = Response->GetContentAsString().TrimStartAndEnd();
    UE_LOG(LogTemp, Log, TEXT("[UID] Received UID: %s"), *UID);
    Callback.ExecuteIfBound(UID);
}

