// Copyright Epic Games, Inc. All Rights Reserved.

#include "VehicleProjectWheelFront.h"
#include "UObject/ConstructorHelpers.h"

UVehicleProjectWheelFront::UVehicleProjectWheelFront()
{
	AxleType = EAxleType::Front;
	bAffectedBySteering = true;
	MaxSteerAngle = 40.f;
}