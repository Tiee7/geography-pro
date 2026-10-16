# 第一章全球贴图试用

当前仅 `01-earth-rotation.html` 使用此目录中的贴图。其他章节继续使用原贴图，待第一章试用确认后再同步。

## 全球底图

- 文件：`earth-blue-marble-4096.jpg`，4096 × 2048，约 1.4 MiB。
- 上游：three-globe 2.31.1 示例图片 `earth-blue-marble.jpg`。
- 固定版本下载地址：<https://cdn.jsdelivr.net/npm/three-globe@2.31.1/example/img/earth-blue-marble.jpg>
- 上游仓库：<https://github.com/vasturiano/three-globe>。
- 上游包的 MIT 许可保留在 `LICENSE-three-globe`；保留原图，未裁切、未重采样。
- SHA-256：`228deba2e4b600146bdcb6cfa359b8ead6aacc2b1c13550a29cd82824cfa1c01`。
- 覆盖完整经纬度：经度 −180° 至 +180°，纬度 +90° 至 −90°；2:1 等距圆柱投影，中央经线为 0°。
- 日间底图随仓库加载，不依赖外部图片 CDN。夜光、法线、海面反光和云层暂沿用原来源。

映射使用地球局部法线，避免世界坐标取样导致大陆停留在原地。第一章采用右手 Y 轴向上坐标：0° 经线为 +X，90°E 为 −Z，避免左右镜像；城市、地方时标签、时区和自转箭头均使用此约定。经度 `atan(-z,x)`，纬度 `asin(y)`；Three.js 默认 `flipY=true`，所以 `u=lon/(2π)+0.5`、`v=lat/π+0.5`。光照仍使用世界法线，保留晨昏变化；降低海面反光强度，避免高光遮住大片地图。

## 后续国界层

底图没有内嵌国界。本次不加载和显示国界，以便先确认大陆完整性、方向和自转。

已检查可用的候选数据：Natural Earth Vector v5.1.2，公共领域，`ne_110m_admin_0_countries.geojson`（177 个 Polygon/MultiPolygon 要素）。

- 数据：<https://cdn.jsdelivr.net/gh/nvkelso/natural-earth-vector@v5.1.2/geojson/ne_110m_admin_0_countries.geojson>
- 项目及数据说明：<https://github.com/nvkelso/natural-earth-vector/tree/v5.1.2>

后续可将边界单独渲染为可开关的矢量线层，按同一经纬度坐标转换到球面，随地球一起自转。110m 适合全球视角，更精细的课堂定位可选 50m 或 10m。接入前需要确认课程采用的国界版本和争议地区表达；候选数据尚未作为课程国界定稿。

## 第一章试用检查

1. 暂停后拖动球体，核对美洲、欧亚非、澳洲及南极均存在，北方在北。
2. 打开自转，确认大陆和参照城市一起移动，晨昏圈仍随太阳方向显示。
3. 可关闭云层和辉光以查看海岸线；夜半球变暗是昼夜演示效果。
4. 不要在第一章试用确认前改动其他课程。
