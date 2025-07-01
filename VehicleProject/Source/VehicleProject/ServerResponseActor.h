// Fill out your copyright notice in the Description page of Project Settings.

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "Http.h"
#include "ServerResponseActor.generated.h"

DECLARE_DYNAMIC_DELEGATE_OneParam(FOnUidReceived, const FString&, UID);

UCLASS()
class VEHICLEPROJECT_API AServerResponseActor : public AActor
{
	GENERATED_BODY()
	
public:	
	// Sets default values for this actor's properties
	AServerResponseActor();

	UPROPERTY(EditAnywhere,BlueprintReadOnly)
	FString UID;

protected:
	// Called when the game starts or when spawned
	virtual void BeginPlay() override;

public:	
	// Called every frame
	virtual void Tick(float DeltaTime) override;

	/** GET /last_uid/ 요청 후 UID 문자열을 OnSuccess 델리게이트로 반환 */
	UFUNCTION(BlueprintCallable, Category = "DiffusionAPI")
	void GetLastUIDFromServer(const FOnUidReceived& OnSuccess);

private:
	void OnLastUIDResponse(FHttpRequestPtr Request, FHttpResponsePtr Response, bool bWasSuccessful, FOnUidReceived Callback);
};
