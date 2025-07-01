// Copyright Epic Games, Inc. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "VehicleProjectPawn.h"
#include "VehicleProjectSportsCar.generated.h"

/**
 *  Sports car wheeled vehicle implementation
 */
UCLASS(abstract)
class VEHICLEPROJECT_API AVehicleProjectSportsCar : public AVehicleProjectPawn
{
	GENERATED_BODY()
	
public:

	AVehicleProjectSportsCar();
};
