from sd_generator import StableDiffusionGenerator
from background_remover import BackgroundRemover

def generate_object_image_without_bg(prompt, sd_generator:StableDiffusionGenerator, bg_remover:BackgroundRemover, save_path="output.png"):
    img = sd_generator.generate(prompt)
    img_nobg = bg_remover.remove_background(img)
    img_nobg.save(save_path)
    return img_nobg

if __name__ == "__main__":
    # 1. 초기화
    sd_gen = StableDiffusionGenerator(model_name="stabilityai/stable-diffusion-2-1", device="cuda")
    bg_remover = BackgroundRemover()

    # 2. 객체 생성 및 배경 제거
    prompt = "a futuristic dog, isometric, green background"
    img_nobg = generate_object_image_without_bg(prompt, sd_gen, bg_remover, save_path="robotdog.png")