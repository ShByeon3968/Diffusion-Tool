// Fill out your copyright notice in the Description page of Project Settings.

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "Http.h"
#include "HttpModule.h"
#include "ServerRequestActor.generated.h"

// ����������������������������������������������������������������
// ��������Ʈ ����
// ����������������������������������������������������������������
/*

*/
DECLARE_DYNAMIC_DELEGATE_OneParam(FOnMeshGeneratedDynamic, const FString&, UID);
/**
 * �̹��� �ٿ�ε� �Ϸ� �� ȣ��
 * @param FilePath ����� �̹��� ���
 * @param bSuccess ���� ����
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

	// Blueprint���� ���� ������ GLB ���
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
