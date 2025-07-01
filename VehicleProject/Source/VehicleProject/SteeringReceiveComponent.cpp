// Fill out your copyright notice in the Description page of Project Settings.


#include "SteeringReceiveComponent.h"

// Sets default values for this component's properties
USteeringReceiveComponent::USteeringReceiveComponent()
{
	// Set this component to be initialized when the game starts, and to be ticked every frame.  You can turn these features
	// off to improve performance if you don't need them.
	PrimaryComponentTick.bCanEverTick = true;

	// ...
}


// Called when the game starts
void USteeringReceiveComponent::BeginPlay()
{
	Super::BeginPlay();

	// 바인딩할 주소/포트
	FIPv4Address Addr;
	FIPv4Address::Parse(TEXT("127.0.0.1"), Addr);
	Endpoint = FIPv4Endpoint(Addr, 5005);

	RemoteAddr = ISocketSubsystem::Get(PLATFORM_SOCKETSUBSYSTEM)->CreateInternetAddr();
	
	ListenSocket = FUdpSocketBuilder(TEXT("UDPReceiverSocket"))
		.AsNonBlocking()
		.AsReusable()
		.BoundToEndpoint(Endpoint)
		.WithReceiveBufferSize(2 * 1024 * 1024);

	if (ListenSocket)
	{
		UE_LOG(LogTemp, Warning, TEXT("UDP Socket Bind Success"));
	}
	else
	{
		UE_LOG(LogTemp, Error, TEXT("Failed to bind UDP socket"));
	}
}


// Called every frame
void USteeringReceiveComponent::TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction)
{
	Super::TickComponent(DeltaTime, TickType, ThisTickFunction);
	ReceiveData();
	// ...
}

void USteeringReceiveComponent::EndPlay(const EEndPlayReason::Type EndPlayReason)
{
	if (ListenSocket)
	{
		ListenSocket->Close();
		ISocketSubsystem::Get(PLATFORM_SOCKETSUBSYSTEM)->DestroySocket(ListenSocket);
	}

	Super::EndPlay(EndPlayReason);
}

void USteeringReceiveComponent::ReceiveData()
{
	UE_LOG(LogTemp, Warning, TEXT("ReceiveData called"));
	if (!ListenSocket) return;

	uint32 Size;
	while (ListenSocket->HasPendingData(Size))
	{
		TArray<uint8> Data;
		Data.SetNumUninitialized(FMath::Min(Size, 65507u));
		int32 Read = 0;
		ListenSocket->Recv(Data.GetData(), Data.Num(), Read);

		FString Received = FString(ANSI_TO_TCHAR(reinterpret_cast<const char*>(Data.GetData())));
		LatestSteeringValue = FCString::Atof(*Received);

		UE_LOG(LogTemp, Log, TEXT("Received steering: %f"), LatestSteeringValue);
	}
}

