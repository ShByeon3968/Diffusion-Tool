from sd_generator import DiffusionGenerator,SanaGenerator
from background_remover import BackgroundRemover

def generate_object_image_without_bg(prompt, sd_generator:DiffusionGenerator, bg_remover:BackgroundRemover, save_path="output.png"):
    img = sd_generator.generate(prompt)
    img_nobg = bg_remover.remove_background(img)
    img_nobg.save(save_path)
    return img_nobg

if __name__ == "__main__":
    # 1. 초기화
    sd_gen = SanaGenerator()
    bg_remover = BackgroundRemover()

    # 2. 객체 생성 및 배경 제거
    prompt = "a cyberpunk cat with a neon sign "
    img = sd_gen.generate(prompt)
    img[0].save("output.png")