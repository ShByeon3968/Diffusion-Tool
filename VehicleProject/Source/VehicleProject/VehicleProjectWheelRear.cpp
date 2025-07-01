// Copyright Epic Games, Inc. All Rights Reserved.

#include "VehicleProjectWheelRear.h"
#include "UObject/ConstructorHelpers.h"

UVehicleProjectWheelRear::UVehicleProjectWheelRear()
{
	AxleType = EAxleType::Rear;
	bAffectedByHandbrake = true;
	bAffectedByEngine = true;
}