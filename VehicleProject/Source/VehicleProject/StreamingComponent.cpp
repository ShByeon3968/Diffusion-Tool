// Fill out your copyright notice in the Description page of Project Settings.


#include "StreamingComponent.h"
#include "Sockets.h"
#include "SocketSubsystem.h"
#include "IPAddress.h"
#include "IImageWrapperModule.h"
#include "IImageWrapper.h"
#include "Modules/ModuleManager.h"

// Sets default values for this component's properties
UStreamingComponent::UStreamingComponent()
{
	// Set this component to be initialized when the game starts, and to be ticked every frame.  You can turn these features
	// off to improve performance if you don't need them.
	PrimaryComponentTick.bCanEverTick = true;

	// ...
}


// Called when the game starts
void UStreamingComponent::BeginPlay()
{
	Super::BeginPlay();
	InitializeSocket();
	
}

void UStreamingComponent::EndPlay(const EEndPlayReason::Type EndPlayReason)
{
	if (ListenSocket)
	{
		ListenSocket->Close();
		ISocketSubsystem::Get(PLATFORM_SOCKETSUBSYSTEM)->DestroySocket(ListenSocket);
		ListenSocket = nullptr;
	}
	Super::EndPlay(EndPlayReason);
}


// Called every frame
void UStreamingComponent::TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction)
{
	Super::TickComponent(DeltaTime, TickType, ThisTickFunction);

	// ...
}

void UStreamingComponent::ReceiveJPEGData()
{
	if (!ListenSocket) return;

	uint32 Size;
	while (ListenSocket->HasPendingData(Size))
	{
		TArray<uint8> Data;
		Data.SetNumUninitialized(FMath::Min(Size, 65507u));
		int32 Read = 0;
		ListenSocket->Recv(Data.GetData(), Data.Num(), Read);
		UpdateTexture(Data);
	}
}

UTexture2D* UStreamingComponent::GetReceivedTexture()
{
	return ReceivedTexture;
}

void UStreamingComponent::InitializeSocket()
{
	FIPv4Address Addr;
	FIPv4Address::Parse(TEXT("127.0.0.1"), Addr);
	Endpoint = FIPv4Endpoint(Addr, 10000);

	ListenSocket = FUdpSocketBuilder(TEXT("UDPImageReceiverSocket"))
		.AsNonBlocking()
		.AsReusable()
		.BoundToEndpoint(Endpoint)
		.WithReceiveBufferSize(2 * 1024 * 1024);

	if (ListenSocket)
	{
		UE_LOG(LogTemp, Warning, TEXT("UDP JPEG Socket Bind Success"));
	}
	else
	{
		UE_LOG(LogTemp, Error, TEXT("Failed to bind JPEG UDP socket"));
	}
}

void UStreamingComponent::UpdateTexture(const TArray<uint8>& JPEGData)
{
	IImageWrapperModule& ImageWrapperModule = FModuleManager::LoadModuleChecked<IImageWrapperModule>(FName("ImageWrapper"));
	TSharedPtr<IImageWrapper> ImageWrapper = ImageWrapperModule.CreateImageWrapper(EImageFormat::JPEG);

	if (ImageWrapper.IsValid() && ImageWrapper->SetCompressed(JPEGData.GetData(), JPEGData.Num()))
	{
		TArray64<uint8> UncompressedRGBA;
		if (ImageWrapper->GetRaw(ERGBFormat::BGRA, 8, UncompressedRGBA))
		{
			int32 Width = ImageWrapper->GetWidth();
			int32 Height = ImageWrapper->GetHeight();

			if (!ReceivedTexture || ReceivedTexture->GetSizeX() != Width || ReceivedTexture->GetSizeY() != Height)
			{
				ReceivedTexture = UTexture2D::CreateTransient(Width, Height);
				ReceivedTexture->UpdateResource();
			}

			void* TextureData = ReceivedTexture->GetPlatformData()->Mips[0].BulkData.Lock(LOCK_READ_WRITE);
			FMemory::Memcpy(TextureData, UncompressedRGBA.GetData(), UncompressedRGBA.Num());
			ReceivedTexture->GetPlatformData()->Mips[0].BulkData.Unlock();
			ReceivedTexture->UpdateResource();
		}
	}
}

