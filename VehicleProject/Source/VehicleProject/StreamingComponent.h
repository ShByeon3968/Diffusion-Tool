// Fill out your copyright notice in the Description page of Project Settings.

#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "Networking.h"
#include "Engine/Texture2D.h"
#include "StreamingComponent.generated.h"


UCLASS( ClassGroup=(Custom), meta=(BlueprintSpawnableComponent) )
class VEHICLEPROJECT_API UStreamingComponent : public UActorComponent
{
	GENERATED_BODY()

public:	
	// Sets default values for this component's properties
	UStreamingComponent();

protected:
	// Called when the game starts
	virtual void BeginPlay() override;
	virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;

public:	
	// Called every frame
	virtual void TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction) override;

	UFUNCTION(BlueprintCallable)
	void ReceiveJPEGData();
	UFUNCTION(BlueprintCallable, Category = "ImageStreaming")
	UTexture2D* GetReceivedTexture();

private:
	FSocket* ListenSocket;
	FIPv4Endpoint Endpoint;

	UPROPERTY(BlueprintReadOnly, VisibleAnywhere, meta = (AllowPrivateAccess = true))
	UTexture2D* ReceivedTexture;

	void InitializeSocket();
	void UpdateTexture(const TArray<uint8>& JPEGData);
		
};
