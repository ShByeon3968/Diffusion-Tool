from sd_generator import CarGenerator

sd = CarGenerator()
image = sd.generate("a realistic black car, detailed, white background", negative_prompt="bad quality, blurry, worse quality")
image.save("test.png")