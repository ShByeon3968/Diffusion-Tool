// Fill out your copyright notice in the Description page of Project Settings.

#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "Sockets.h"
#include "Networking.h"
#include "SteeringReceiveComponent.generated.h"


UCLASS( ClassGroup=(Custom), meta=(BlueprintSpawnableComponent) )
class VEHICLEPROJECT_API USteeringReceiveComponent : public UActorComponent
{
	GENERATED_BODY()

public:	
	// Sets default values for this component's properties
	USteeringReceiveComponent();

protected:
	// Called when the game starts
	virtual void BeginPlay() override;

public:	
	// Called every frame
	virtual void TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction) override;
	virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;
	
	UPROPERTY(EditAnyWhere,BlueprintReadWrite)
	float LatestSteeringValue = 0.0f;

private:
	FSocket* ListenSocket;
	FIPv4Endpoint Endpoint;
	TSharedPtr<FInternetAddr> RemoteAddr;

	UFUNCTION(BlueprintCallable)
	void ReceiveData();
		
};
