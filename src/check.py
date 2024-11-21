import cv2
data = {
	"Vectors": [
		{
			"X": 507.40597534179688,
			"Y": 350.667236328125
		},
		{
			"X": 521.21600341796875,
			"Y": 347.60662841796875
		},
		{
			"X": 389.99658203125,
			"Y": 349.91226196289062
		},
		{
			"X": 507.40597534179688,
			"Y": 398.09548950195312
		},
		{
			"X": 362.57815551757812,
			"Y": 346.239013671875
		},
		{
			"X": 521.21600341796875,
			"Y": 410.588623046875
		},
		{
			"X": 389.99658203125,
			"Y": 401.17721557617188
		},
		{
			"X": 362.57815551757812,
			"Y": 416.17111206054688
		}
	]
}

# X, Y 좌표 추출
x_coords = [vector['X'] for vector in data['Vectors']]
y_coords = [vector['Y'] for vector in data['Vectors']]
bbox = [216,346,139,70]
# xmin, xmax, ymin, ymax 계산
xmin = 602
xmax = 601+172
ymin = 348
ymax = 348+60

image = cv2.imread('Resource/1/1_frame_59.jpg')

# 사각형 그리기
rectangle_color = (0, 255, 0)  # 녹색
thickness = 2  # 선 두께
cv2.rectangle(image, (xmin, ymin), (xmax, ymax), rectangle_color, thickness)

# 결과 이미지 표시
cv2.imshow("Rectangle on Image", image)
cv2.waitKey(0)
cv2.destroyAllWindows()