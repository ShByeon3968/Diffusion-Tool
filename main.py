from sd_generator import DiffusionGenerator,SanaGenerator
from background_remover import BackgroundRemover
from image_to_3d import MVSGenerator, MeshGenerator
import matplotlib.pyplot as plt
import trimesh

def generate_object_image_without_bg(prompt, sd_generator:DiffusionGenerator, bg_remover:BackgroundRemover, save_path="output.png"):
    img = sd_generator.generate(prompt)
    img_nobg = bg_remover.remove_background(img[0])
    img_nobg.save(save_path)
    return img_nobg

if __name__ == "__main__":
    # 1.SANA 초기화
    sd_gen = SanaGenerator()

    # 2. 객체 이미지 생성
    out_image_path = "./output/output_diffusion.png"
    prompt = "a cup of coffee, white background"
    image = sd_gen.generate(prompt)[0]
    image.save(out_image_path)
    plt.imshow(image)
    plt.axis('off')
    plt.show()

    # 3. Mutli-View Stereo (MVS) 생성
    mvs_gen = MVSGenerator(input_image_path=out_image_path)
    mv_images, mv_show_image = mvs_gen.excute()
    mv_images.save("./output/output_mvs_coffe.png")
    plt.imshow(mv_images)
    plt.axis('off')
    plt.show()
    # 4. Instant Mesh 생성
    mesh_gen = MeshGenerator()
    mesh_gen.excute(mv_images,'./output/mesh_coffee/')

# "a futuristic robot dog,black, isometric, white background"