import sys
import os
import numpy as np
import open3d as o3d
import trimesh
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QVBoxLayout,
    QPushButton, QDoubleSpinBox, QFileDialog
)

class MeshEditorApp(QMainWindow):
    def __init__(self, obj_path=None, auto_run=False):
        super().__init__()
        self.setWindowTitle("Mesh Editor with GLB Export")
        self.setGeometry(300, 300, 400, 200)

        self.obj_path = obj_path
        self.auto_run = auto_run

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        layout = QVBoxLayout()
        self.central_widget.setLayout(layout)

        self.label = QLabel("삭제 반경 설정 (단위: m):")
        layout.addWidget(self.label)

        self.radius_spinbox = QDoubleSpinBox()
        self.radius_spinbox.setRange(0.01, 1.0)
        self.radius_spinbox.setSingleStep(0.01)
        self.radius_spinbox.setValue(0.1)
        layout.addWidget(self.radius_spinbox)

        self.edit_button = QPushButton("메쉬 편집 시작")
        self.edit_button.clicked.connect(self.start_editing)
        layout.addWidget(self.edit_button)

        self.status_label = QLabel("상태 메시지")
        layout.addWidget(self.status_label)

        if self.auto_run and self.obj_path:
            self.start_editing()

    def start_editing(self):
        if not self.obj_path:
            file_path, _ = QFileDialog.getOpenFileName(self, "메쉬 파일 선택", "", "3D Files (*.obj *.glb)")
            if not file_path:
                return
            self.obj_path = file_path

        radius = self.radius_spinbox.value()
        self.status_label.setText(f"반경 {radius:.2f}m로 정점 선택 중...")

        mesh, pcd = self.load_mesh_and_convert(self.obj_path)
        picked_idx = self.pick_point(pcd)

        if picked_idx is None:
            self.status_label.setText("❌ 정점이 선택되지 않았습니다.")
            return

        center_point = np.asarray(pcd.points)[picked_idx]
        distances = np.linalg.norm(np.asarray(pcd.points) - center_point, axis=1)
        delete_mask = distances < radius

        # 삭제 대상 표시
        colors = np.tile([0.7, 0.7, 0.7], (len(pcd.points), 1))
        colors[delete_mask] = [1.0, 0.0, 0.0]
        pcd.colors = o3d.utility.Vector3dVector(colors)

        confirmed = self.preview_deletion(pcd)
        if confirmed:
            edited_mesh = self.delete_vertices_near(mesh, center_point, radius)
            out_path = self.obj_path.replace(".obj", "_edited.glb").replace(".glb", "_edited.glb")
            self.export_mesh_to_glb(edited_mesh, out_path)
            self.status_label.setText(f"✅ GLB 저장 완료: {out_path}")
        else:
            self.status_label.setText("⛔ 삭제 취소됨")

    def load_mesh_and_convert(self, path):
        mesh = o3d.io.read_triangle_mesh(path)
        mesh.compute_vertex_normals()
        mesh.paint_uniform_color([0.7, 0.7, 0.7])

        pcd = o3d.geometry.PointCloud()
        pcd.points = mesh.vertices
        pcd.colors = o3d.utility.Vector3dVector(
            np.tile([0.7, 0.7, 0.7], (len(pcd.points), 1))
        )
        return mesh, pcd

    def pick_point(self, pcd):
        vis = o3d.visualization.VisualizerWithEditing()
        vis.create_window(window_name="정점 선택 (Shift+Click 후 Q)", width=800, height=600)
        vis.add_geometry(pcd)
        vis.run()
        vis.destroy_window()
        picked = vis.get_picked_points()
        return picked[0] if picked else None

    def preview_deletion(self, pcd):
        vis = o3d.visualization.VisualizerWithKeyCallback()
        vis.create_window(window_name="삭제 미리보기 (Y:확인 N:취소)", width=800, height=600)
        vis.add_geometry(pcd)

        self.confirm_delete = None

        def key_y(vis):
            self.confirm_delete = True
            vis.close()
            return False

        def key_n(vis):
            self.confirm_delete = False
            vis.close()
            return False

        vis.register_key_callback(ord("Y"), key_y)
        vis.register_key_callback(ord("N"), key_n)
        vis.run()
        vis.destroy_window()
        return self.confirm_delete

    def delete_vertices_near(self, mesh, center, radius):
        vertices = np.asarray(mesh.vertices)
        distances = np.linalg.norm(vertices - center, axis=1)
        to_delete = np.where(distances < radius)[0]
        print(f"🗑️ 삭제된 정점 수: {len(to_delete)}")
        mesh.remove_vertices_by_index(to_delete)
        return mesh

    def export_mesh_to_glb(self, mesh: o3d.geometry.TriangleMesh, out_path: str):
        trimesh_mesh = trimesh.Trimesh(
            vertices=np.asarray(mesh.vertices),
            faces=np.asarray(mesh.triangles),
            process=False
        )
        scene = trimesh.Scene(trimesh_mesh)
        scene.export(out_path)
        print(f"[GLB] Exported to {out_path}")

def run_mesh_editor(obj_path=None, auto_run=False):
    app = QApplication(sys.argv)
    window = MeshEditorApp(obj_path=obj_path, auto_run=auto_run)
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":

    run_mesh_editor("src/output/fastapi/88b2f595/mesh/mesh_6c5401d3.glb",auto_run=True)