import sys
import open3d as o3d
import numpy as np
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QVBoxLayout,
    QPushButton, QDoubleSpinBox, QFileDialog
)

class MeshEditorApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Mesh Editor with Red Highlight Preview")
        self.setGeometry(300, 300, 400, 200)

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

        self.edit_button = QPushButton("OBJ 메쉬 편집 시작")
        self.edit_button.clicked.connect(self.start_editing)
        layout.addWidget(self.edit_button)

        self.status_label = QLabel("")
        layout.addWidget(self.status_label)

    def start_editing(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "메쉬 파일 선택", "", "OBJ Files (*.obj)")
        if not file_path:
            return

        radius = self.radius_spinbox.value()
        self.status_label.setText(f"반경 {radius:.2f}m로 정점 선택 중...")

        mesh, pcd = self.load_mesh_and_convert(file_path)
        picked_idx = self.pick_point(pcd)

        if picked_idx is None:
            self.status_label.setText("❌ 정점이 선택되지 않았습니다.")
            return

        center_point = np.asarray(pcd.points)[picked_idx]
        distances = np.linalg.norm(np.asarray(pcd.points) - center_point, axis=1)
        delete_mask = distances < radius

        # 색상 변경: 삭제 대상만 빨간색
        colors = np.tile([0.7, 0.7, 0.7], (len(pcd.points), 1))
        colors[delete_mask] = [1.0, 0.0, 0.0]  # 빨간색 표시
        pcd.colors = o3d.utility.Vector3dVector(colors)

        # 삭제 미리보기 표시
        confirmed = self.preview_deletion(pcd)

        if confirmed:
            edited_mesh = self.delete_vertices_near(mesh, center_point, radius)
            out_path = file_path.replace(".obj", "_edited.ply")
            o3d.io.write_triangle_mesh(out_path, edited_mesh)
            self.status_label.setText(f"✅ 편집 완료: {out_path}")
        else:
            self.status_label.setText("⛔ 삭제 취소됨")

    def load_mesh_and_convert(self, path):
        mesh = o3d.io.read_triangle_mesh(path)
        mesh.compute_vertex_normals()
        mesh.paint_uniform_color([0.7, 0.7, 0.7])

        # PointCloud로 변환
        pcd = o3d.geometry.PointCloud()
        pcd.points = mesh.vertices
        pcd.colors = o3d.utility.Vector3dVector(
            np.tile([0.7, 0.7, 0.7], (len(pcd.points), 1))
        )
        return mesh, pcd

    def pick_point(self, pcd):
        vis = o3d.visualization.VisualizerWithEditing()
        vis.create_window(window_name="정점 선택 (Shift+Click → Q)", width=800, height=600)
        vis.add_geometry(pcd)
        vis.run()
        vis.destroy_window()

        picked = vis.get_picked_points()
        return picked[0] if picked else None

    def preview_deletion(self, pcd):
        print("🟥 빨간색으로 표시된 정점이 삭제 예정입니다.")
        print("Y: 삭제 확인 / N: 삭제 취소")

        vis = o3d.visualization.VisualizerWithKeyCallback()
        vis.create_window(window_name="삭제 미리보기", width=800, height=600)
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

def main():
    app = QApplication(sys.argv)
    window = MeshEditorApp()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
