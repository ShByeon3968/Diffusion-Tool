// Copyright Epic Games, Inc. All Rights Reserved.

using UnrealBuildTool;

public class VehicleProject : ModuleRules
{
	public VehicleProject(ReadOnlyTargetRules Target) : base(Target)
	{
		PCHUsage = PCHUsageMode.UseExplicitOrSharedPCHs;

		PublicDependencyModuleNames.AddRange(new string[] { "Core", "CoreUObject", "Engine", "InputCore", "EnhancedInput", "ChaosVehicles", "PhysicsCore" ,"UMG", "Slate", "SlateCore","HTTP", "Json", "JsonUtilities","Sockets", "Networking","WebSockets"});
	}
}
