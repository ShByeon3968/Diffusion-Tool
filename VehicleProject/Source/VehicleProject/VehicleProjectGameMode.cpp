// Copyright Epic Games, Inc. All Rights Reserved.

#include "VehicleProjectGameMode.h"
#include "VehicleProjectPlayerController.h"

AVehicleProjectGameMode::AVehicleProjectGameMode()
{
	PlayerControllerClass = AVehicleProjectPlayerController::StaticClass();
}
