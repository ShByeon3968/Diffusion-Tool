// Fill out your copyright notice in the Description page of Project Settings.

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "Http.h"
#include "HttpModule.h"
#include "ServerRequestActor.generated.h"

// ────────────────────────────────
// 델리게이트 정의
// ────────────────────────────────
/*

*/
DECLARE_DYNAMIC_DELEGATE_OneParam(FOnMeshGeneratedDynamic, const FString&, UID);
/**
 * 이미지 다운로드 완료 시 호출
 * @param FilePath 저장된 이미지 경로
 * @param bSuccess 성공 여부
 */
DECLARE_DYNAMIC_DELEGATE_TwoParams(FOnImageDownloaded, FString, FilePath, bool, bSuccess);

UCLASS()
class VEHICLEPROJECT_API AServerRequestActor : public AActor
{
	GENERATED_BODY()
	
public:	
	// Sets default values for this actor's properties
	AServerRequestActor();

protected:
	// Called when the game starts or when spawned
	virtual void BeginPlay() override;

public:	
	// Called every frame
	virtual void Tick(float DeltaTime) override;

	UFUNCTION(BlueprintCallable)
	void RequestMeshGeneration(const FString& Prompt, const FString& Model, FOnMeshGeneratedDynamic Callback);

	UFUNCTION(BlueprintCallable)
	void RequestImageFromServer(const FString& UID, const FString& Type, const FOnImageDownloaded& Callback);

	// Blueprint에서 접근 가능한 GLB 경로
	UPROPERTY(BlueprintReadOnly, VisibleAnywhere, Category = "GLB Server")
	FString LastReceivedGLBPath;
	UPROPERTY(BlueprintReadOnly, VisibleAnywhere, Category = "GLB Server")
	UTexture2D* GenTexture;

private:
	void OnImageResponseReceived(FHttpRequestPtr Request, FHttpResponsePtr Response, bool bWasSuccessful, FOnImageDownloaded Callback, FString UID, FString Type);

	void OnMeshGenerationResponse(FHttpRequestPtr Request, FHttpResponsePtr Response, bool bWasSuccessful, FOnMeshGeneratedDynamic Callback);
	/*void SpawnGLBMesh(const FString& GlbPath);*/

	UFUNCTION(BlueprintCallable)
	void WaitForImageThenLoad(FString Path);


	FTimerHandle ImageCheckHandle;
	UTexture2D* LoadTextureFromFile(const FString& FilePath);
};
