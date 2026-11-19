import fs from "node:fs/promises";
import path from "node:path";
import { spawnSync } from "node:child_process";
import { fileURLToPath, pathToFileURL } from "node:url";

const scriptDir = path.dirname(fileURLToPath(import.meta.url));
const workspaceDir = path.resolve(scriptDir, "..");
const runtimeNodeModules = "C:/Users/17795/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules";
process.env.RUNTIME_NODE_MODULES = runtimeNodeModules;
const { Presentation, PresentationFile } = await import(pathToFileURL(path.join(runtimeNodeModules, "@oai/artifact-tool/dist/artifact_tool.mjs")).href);
const skillDir = "C:/Users/17795/.codex/plugins/cache/openai-primary-runtime/presentations/26.1026.10807/skills/presentations";
const buildDir = path.join(workspaceDir, ".codex-build", "defense-deck");
const finalizeDir = path.join(workspaceDir, ".codex-build", "defense-final");
const validationDir = path.join(workspaceDir, ".codex-build", "defense-validation");
const outputDir = path.join(workspaceDir, "deliverables");
const draftPath = path.join(buildDir, "defense-draft.pptx");
const finalPath = path.join(finalizeDir, "smart-waste-sorting-defense-current.pptx");
const publishedPath = path.join(outputDir, "smart-waste-sorting-defense-final.pptx");
const pdfPath = path.join(outputDir, "smart-waste-sorting-defense-final.pdf");
const width = 1600;
const height = 900;
const font = "Microsoft YaHei";

await fs.mkdir(buildDir, { recursive: true });
await fs.mkdir(finalizeDir, { recursive: true });
await fs.mkdir(validationDir, { recursive: true });
await fs.mkdir(outputDir, { recursive: true });

const frameScript = String.raw`
import cv2, pathlib, sys
root = pathlib.Path(sys.argv[1])
target = root / '.codex-build' / 'defense-deck'
target.mkdir(parents=True, exist_ok=True)
sources = [
    ('assets/assessment_demo.mp4', (12, 92, 205, 318)),
    ('vedio/dep.mp4', (0, 410, 1180, 2160)),
]
for source, frames in sources:
    capture = cv2.VideoCapture(str(root / source))
    if not capture.isOpened():
        raise RuntimeError('Could not open ' + source)
    for frame_index in frames:
        capture.set(cv2.CAP_PROP_POS_FRAMES, frame_index)
        ok, frame = capture.read()
        if not ok:
            raise RuntimeError('Could not read frame {} from {}'.format(frame_index, source))
        output = target / '{}-{:04}.jpg'.format(pathlib.Path(source).stem, frame_index)
        if not cv2.imwrite(str(output), frame, [cv2.IMWRITE_JPEG_QUALITY, 92]):
            raise RuntimeError('Could not write ' + str(output))
    capture.release()
print('Extracted source frames into', target)
`;
const extraction = spawnSync("python", ["-c", frameScript, workspaceDir], { encoding: "utf8" });
if (extraction.status !== 0) {
  throw new Error(extraction.stderr || extraction.stdout || "Video frame extraction failed");
}
console.log(extraction.stdout.trim());

const presentation = Presentation.create({ slideSize: { width, height } });
const colors = {
  ink: "#183E43",
  inkSoft: "#36595A",
  paper: "#F2F0E4",
  paperLight: "#FBF9F1",
  green: "#638467",
  greenDark: "#365C4A",
  teal: "#398A87",
  blue: "#5197B3",
  amber: "#D89445",
  rust: "#B65E4C",
  olive: "#87914F",
  line: "#BCC8B8",
  muted: "#647776",
  white: "#FFFDF6",
};

function shape(slide, name, geometry, x, y, w, h, fill = "none", lineFill = "none", lineWidth = 0) {
  return slide.shapes.add({
    geometry,
    name,
    position: { left: x, top: y, width: w, height: h },
    fill,
    line: { style: "solid", fill: lineFill, width: lineWidth },
    borderRadius: geometry === "roundRect" ? 8 : undefined,
  });
}

function text(slide, name, content, x, y, w, h, opts = {}) {
  const item = shape(slide, name, "textbox", x, y, w, h);
  item.text = content;
  item.text.insets = 0;
  item.text.style = {
    typeface: font,
    fontSize: opts.size ?? 26,
    color: opts.color ?? colors.ink,
    bold: opts.bold ?? false,
    alignment: opts.align ?? "left",
    verticalAlignment: opts.valign ?? "middle",
    lineSpacing: opts.leading ?? 1.12,
  };
  return item;
}

function baseSlide(title, section, number) {
  const slide = presentation.slides.add();
  slide.background.fill = colors.paper;
  shape(slide, `marker-${number}`, "rect", 0, 0, 14, height, colors.greenDark);
  text(slide, `section-${number}`, section, 74, 48, 380, 28, { size: 16, bold: true, color: colors.teal });
  text(slide, `title-${number}`, title, 74, 88, 1440, 70, { size: 42, bold: true, color: colors.ink });
  shape(slide, `rule-${number}`, "rect", 74, 174, 1450, 2, colors.line);
  text(slide, `page-${number}`, String(number).padStart(2, "0"), 1480, 836, 44, 24, { size: 16, color: colors.muted, align: "right" });
  return slide;
}

async function addImage(slide, name, file, x, y, w, h, alt, fit = "cover") {
  const bytes = await fs.readFile(file);
  const contentType = file.toLowerCase().endsWith(".png")
    ? "image/png"
    : "image/jpeg";
  const blob = bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.byteLength);
  slide.images.add({
    name,
    blob,
    contentType,
    alt,
    fit,
    position: { left: x, top: y, width: w, height: h },
    geometry: "roundRect",
    borderRadius: 8,
  });
}

function note(slide, value) {
  slide.speakerNotes.text = value;
}

function bullet(slide, name, label, body, x, y, w, accent = colors.teal) {
  shape(slide, `${name}-dot`, "ellipse", x, y + 13, 13, 13, accent);
  text(slide, `${name}-label`, label, x + 30, y, w - 30, 32, { size: 23, bold: true, color: colors.ink });
  text(slide, `${name}-body`, body, x + 30, y + 37, w - 34, 54, { size: 18, color: colors.inkSoft, valign: "top", leading: 1.17 });
}

function arrow(slide, name, x, y, w, color = colors.amber) {
  shape(slide, name, "rightArrow", x, y, w, 30, color);
}

// 1. Title slide
{
  const slide = presentation.slides.add();
  slide.background.fill = colors.ink;
  const coverFrame = path.join(buildDir, "assessment_demo-0205.jpg");
  await addImage(slide, "cover-source-video-frame", coverFrame, 760, 0, 840, 900, "比赛演示视频中的垃圾分类样例");
  shape(slide, "cover-paper-field", "rect", 0, 0, 820, 900, colors.ink);
  shape(slide, "cover-accent", "rect", 86, 154, 8, 124, colors.amber);
  text(slide, "cover-title", "智能垃圾\n视觉分拣系统", 122, 150, 600, 190, { size: 56, bold: true, color: colors.white, leading: 1.04 });
  text(slide, "cover-subtitle", "招新考核项目说明", 124, 375, 510, 48, { size: 25, color: "#DCE8D3" });
  shape(slide, "cover-rule", "rect", 124, 462, 360, 2, colors.green);
  text(slide, "cover-flow", "画面识别  →  执行确认  →  完成计数", 124, 492, 570, 48, { size: 21, color: colors.white });
  text(slide, "cover-author", "王吉祥 · 西北工业大学人工智能专业", 124, 812, 580, 28, { size: 17, color: "#C6D7C7" });
  note(slide, "开场约 15 秒：本项目把视觉检测、上位机控制逻辑和下位机通信串成一个可演示的分拣流程。画面使用仓库中的比赛演示视频帧，不代表真实机械臂现场照片。接下来按数据实际流动顺序说明。\n\n演示时用鼠标点击应用开场页左下角的电脑进入工作台。音频为可选项。");
}

// 2. System architecture
{
  const slide = baseSlide("系统链路与职责边界", "01  系统概览", 2);
  const nodes = [
    ["视频 / 摄像头", "宿主输入", colors.green],
    ["OpenCV / 帧桥", "HTTP 摄像头帧", colors.blue],
    ["YOLO", "检测与映射", colors.amber],
    ["分拣状态机", "稳定确认与计数", colors.rust],
    ["TCP / 串口", "协议收发", colors.teal],
    ["下位机", "执行分拣动作", colors.olive],
  ];
  const x0 = 75;
  const nodeW = 204;
  const gap = 36;
  for (let index = 0; index < nodes.length; index += 1) {
    const [title, caption, color] = nodes[index];
    const x = x0 + index * (nodeW + gap);
    shape(slide, `architecture-node-${index}`, "roundRect", x, 302, nodeW, 124, colors.paperLight, color, 3);
    shape(slide, `architecture-band-${index}`, "rect", x, 302, nodeW, 8, color);
    text(slide, `architecture-title-${index}`, title, x + 12, 330, nodeW - 24, 36, { size: 23, bold: true, align: "center" });
    text(slide, `architecture-caption-${index}`, caption, x + 12, 374, nodeW - 24, 28, { size: 17, color: colors.muted, align: "center" });
    if (index < nodes.length - 1) arrow(slide, `architecture-arrow-${index}`, x + nodeW + 4, 347, 28);
  }
  shape(slide, "ui-observation-line", "rect", 160, 544, 1265, 3, colors.line);
  shape(slide, "ui-observation-branch", "rect", 790, 426, 3, 118, colors.line);
  shape(slide, "ui-observation", "roundRect", 474, 570, 640, 106, "#E4ECE1", colors.green, 2);
  text(slide, "ui-observation-title", "PyQt 工作台", 504, 584, 240, 34, { size: 24, bold: true, color: colors.greenDark });
  text(slide, "ui-observation-copy", "浏览器通过 noVNC 显示 PyQt 工作台、分类计数与 TX / RX 日志", 504, 624, 580, 30, { size: 18, color: colors.inkSoft });
  text(slide, "architecture-boundary", "识别结果由上位机产生；机械动作由下位机执行并回报完成。", 112, 728, 1340, 42, { size: 24, bold: true, color: colors.ink });
  note(slide, "约 25 秒：先讲清楚数据从视频或摄像头进入 OpenCV，再由 YOLO 检测。状态机把检测变成有序指令，TCP 或串口传给下位机。PyQt 是观察和操作入口，不代替下位机动作。\n\n演示时指出工作台里视频画面、四类统计、满载状态和 TX/RX 日志。");
}

// 3. Vision and frame source
{
  const slide = baseSlide("视频帧如何变成分类结果", "02  视觉输入", 3);
  await addImage(slide, "vision-example-frame", path.join(buildDir, "assessment_demo-0092.jpg"), 78, 226, 715, 444, "演示视频中的实际输入帧");
  text(slide, "vision-image-caption", "来自 assets/assessment_demo.mp4 的输入画面", 82, 686, 690, 28, { size: 16, color: colors.muted });
  bullet(slide, "vision-source", "统一帧接口", "视频直接读取，Docker 摄像头经宿主机 JPEG 桥进入同一套 OpenCV 路径。", 868, 235, 605, colors.green);
  bullet(slide, "vision-model", "YOLO 推理", "加载 Predict/best.pt，提取类别、置信度和边界框。", 868, 370, 605, colors.blue);
  bullet(slide, "vision-map", "类别映射", "把训练类别映射到可回收、厨余、有害和其他四类。", 868, 505, 605, colors.amber);
  bullet(slide, "vision-filter", "置信度筛选", "默认阈值 0.50，低于阈值的结果不会进入状态机。", 868, 640, 605, colors.rust);
  note(slide, "约 30 秒：展示仓库测试视频的一帧。OpenCV 读帧后，detector 调用 YOLO predict。适配层把张量坐标和类别转成项目统一的 Detection，并按置信度排序。默认阈值是 0.50。\n\n这次工作没有训练模型。模型类别名称必须在映射表中；未配置类别会在模型适配阶段暴露出来，避免静默分错。");
}

// 4. Protocol
{
  const slide = baseSlide("二进制协议：一帧怎样可靠到达", "03  通信协议", 4);
  const segments = [
    ["AA 55", "帧头", 160, colors.ink],
    ["03", "长度", 116, colors.blue],
    ["01", "命令", 140, colors.amber],
    ["11 03", "序号 + 垃圾类", 286, colors.teal],
    ["18", "校验和", 160, colors.rust],
  ];
  let x = 90;
  for (let index = 0; index < segments.length; index += 1) {
    const [value, caption, widthValue, color] = segments[index];
    shape(slide, `packet-field-${index}`, "rect", x, 264, widthValue, 91, color);
    text(slide, `packet-value-${index}`, value, x + 5, 272, widthValue - 10, 44, { size: 27, bold: true, color: colors.white, align: "center" });
    text(slide, `packet-label-${index}`, caption, x + 4, 318, widthValue - 8, 28, { size: 15, color: colors.white, align: "center" });
    x += widthValue + 16;
  }
  text(slide, "packet-example-label", "完整示例", 92, 405, 190, 30, { size: 18, bold: true, color: colors.teal });
  text(slide, "packet-example", "AA 55 03 01 11 03 18", 90, 446, 900, 72, { size: 38, bold: true, color: colors.ink });
  text(slide, "packet-checksum", "校验 = (03 + 01 + 11 + 03) & FF = 18", 94, 528, 870, 40, { size: 22, color: colors.inkSoft });
  shape(slide, "parser-divider", "rect", 1020, 228, 2, 434, colors.line);
  bullet(slide, "protocol-fragment", "分片 / 粘连", "保留未收完字节；一次读到多帧就逐帧解析。", 1070, 243, 440, colors.blue);
  bullet(slide, "protocol-noise", "噪声 / 坏校验", "丢弃可疑字节并重新寻找 AA 55 帧头。", 1070, 374, 440, colors.rust);
  bullet(slide, "protocol-retry", "相同序号重试", "下位机对已处理序号只重发应答，不重复驱动。", 1070, 505, 440, colors.green);
  text(slide, "protocol-commands", "WASTE_RESULT  ·  ACK  ·  ACTION_DONE  ·  BIN_FULL  ·  START_COMPRESS", 90, 724, 1410, 34, { size: 18, bold: true, color: colors.inkSoft });
  note(slide, "约 35 秒：按字段说明示例。LENGTH 的值是命令和负载总字节数，校验和累加 LENGTH、COMMAND 和 PAYLOAD 后取低 8 位。StreamParser 要处理 TCP 的分片、粘连、噪声和错校验。\n\n强调重发沿用原序号；协议要求下位机做去重。若硬件固件没有这个能力，就不能仅凭上位机重发逻辑保证机械动作只执行一次。");
}

// 5. Controller lifecycle
{
  const slide = baseSlide("状态机把识别变成一次可确认的动作", "04  分拣控制", 5);
  const states = [
    ["IDLE", "连续 3 帧同类", colors.green],
    ["WAIT_ACK", "发送分类 + 序号", colors.blue],
    ["EXECUTING", "等待动作完成", colors.amber],
    ["COOLDOWN", "目标离开后再布防", colors.rust],
  ];
  for (let index = 0; index < states.length; index += 1) {
    const [name, caption, color] = states[index];
    const x = 85 + index * 370;
    shape(slide, `state-${index}`, "roundRect", x, 285, 294, 142, colors.paperLight, color, 3);
    shape(slide, `state-top-${index}`, "rect", x, 285, 294, 9, color);
    text(slide, `state-name-${index}`, name, x + 16, 317, 262, 38, { size: 25, bold: true, color, align: "center" });
    text(slide, `state-caption-${index}`, caption, x + 16, 365, 262, 40, { size: 18, color: colors.inkSoft, align: "center" });
    if (index < states.length - 1) arrow(slide, `state-arrow-${index}`, x + 310, 342, 48);
  }
  text(slide, "ack-guard", "ACK", 489, 455, 135, 31, { size: 19, bold: true, color: colors.blue, align: "center" });
  text(slide, "done-guard", "匹配序号的 ACTION_DONE", 830, 455, 310, 31, { size: 19, bold: true, color: colors.rust, align: "center" });
  shape(slide, "counter-bar", "roundRect", 118, 564, 482, 102, "#E4ECE1", colors.green, 2);
  text(slide, "counter-title", "计数 +1", 142, 579, 160, 37, { size: 28, bold: true, color: colors.greenDark });
  text(slide, "counter-copy", "只在动作完成回报后更新", 142, 619, 400, 28, { size: 18, color: colors.inkSoft });
  shape(slide, "retry-bar", "roundRect", 638, 564, 382, 102, "#E3EBEF", colors.blue, 2);
  text(slide, "retry-title", "超时重试", 664, 579, 160, 37, { size: 27, bold: true, color: colors.ink });
  text(slide, "retry-copy", "最多 2 次，沿用同一序号", 664, 619, 320, 28, { size: 18, color: colors.inkSoft });
  shape(slide, "full-bin-bar", "roundRect", 1058, 564, 422, 102, "#F1E5D7", colors.amber, 2);
  text(slide, "full-bin-title", "满桶拦截", 1082, 579, 160, 37, { size: 27, bold: true, color: colors.ink });
  text(slide, "full-bin-copy", "压缩达到配置阈值时触发", 1082, 619, 370, 28, { size: 18, color: colors.inkSoft });
  text(slide, "state-principle", "识别成功不等于分拣成功；计数跟随设备确认。", 150, 730, 1280, 42, { size: 26, bold: true, color: colors.ink });
  note(slide, "约 35 秒：IDLE 中连续同类达到 3 帧才发送。ACK 让状态进入执行，动作完成消息需要匹配当前序号。计数只在 ACTION_DONE 后更新，随后进入 COOLDOWN，等连续看不到目标才重新布防。\n\n超时最多重试两次，同一序号重发。满桶分类不再下发。计数达到配置阈值后，状态机发压缩命令。");
}

// 6. UI and background processing
{
  const slide = baseSlide("工作台与后台线程", "05  交互与稳定性", 6);
  await addImage(slide, "workbench-input-frame", path.join(workspaceDir, "assets", "workbench_preview.png"), 82, 230, 650, 390, "新版蓝白花卉工作台");
  text(slide, "workbench-image-caption", "新版蓝白花卉工作台，郊野入口与全部操作完整保留", 84, 634, 632, 32, { size: 20, bold: true, color: colors.ink });
  text(slide, "workbench-controls", "视频控制 · 摄像头桥 · 背景音乐 · 返回郊野", 84, 676, 635, 28, { size: 17, color: colors.muted });
  shape(slide, "worker-ui-shell", "roundRect", 804, 234, 682, 114, "#E2EAE0", colors.green, 2);
  text(slide, "worker-ui-title", "PyQt + noVNC", 836, 254, 330, 34, { size: 24, bold: true, color: colors.greenDark });
  text(slide, "worker-ui-copy", "浏览器显示工作台；视频、摄像头、计数和日志共用一套状态", 836, 298, 620, 28, { size: 18, color: colors.inkSoft });
  arrow(slide, "worker-flow-down", 1100, 367, 54, colors.amber);
  shape(slide, "worker-thread-shell", "roundRect", 804, 421, 682, 114, "#E3EBEF", colors.blue, 2);
  text(slide, "worker-thread-title", "QThread 工作线程", 836, 441, 350, 34, { size: 24, bold: true, color: colors.blue });
  text(slide, "worker-thread-copy", "视频/摄像头取帧 · YOLO 推理 · 通信轮询 · 资源释放", 836, 485, 620, 28, { size: 18, color: colors.inkSoft });
  shape(slide, "replay-rule", "roundRect", 804, 584, 682, 106, "#F0E7D8", colors.amber, 2);
  text(slide, "replay-rule-title", "视频重播", 836, 600, 190, 33, { size: 24, bold: true, color: colors.ink });
  text(slide, "replay-rule-copy", "复用 VideoCapture 跳回第 0 帧；清空候选，保留确认计数。", 836, 641, 602, 34, { size: 18, color: colors.inkSoft });
  note(slide, "约 30 秒：应用有郊野开场和项目工作台两种视角。鼠标点击电脑进入工作台，顶部云朵按钮返回。声音设置是可选的，音乐默认关闭。\n\n耗时的读帧、推理和通信在 QThread 运行；界面只处理信号并显示最新结果。场景动画在回到工作台后隐藏并停表。重播复用同一个 VideoCapture，并把状态机当作新输入流重新布防；已经确认的统计保留。");
}

// 7. Deployment
{
  const slide = baseSlide("普通电脑与 Jetson Nano 部署", "06  部署方式", 7);
  text(slide, "pc-heading", "普通电脑演示", 93, 244, 560, 40, { size: 27, bold: true, color: colors.ink });
  shape(slide, "pc-app", "roundRect", 96, 312, 364, 126, "#E4ECE1", colors.green, 2);
  text(slide, "pc-app-label", "上位机容器\nPyQt + YOLO CPU\n浏览器 noVNC", 122, 323, 310, 100, { size: 19, bold: true, color: colors.greenDark, align: "center" });
  shape(slide, "pc-sim", "roundRect", 96, 492, 364, 126, "#E3EBEF", colors.blue, 2);
  text(slide, "pc-sim-label", "TCP 下位机模拟器\n独立服务 / 端口 9000", 122, 510, 310, 85, { size: 20, bold: true, color: colors.ink, align: "center" });
  shape(slide, "pc-network", "rect", 275, 438, 3, 54, colors.amber);
  text(slide, "pc-net-label", "host.docker.internal", 293, 447, 210, 28, { size: 15, color: colors.muted });
  text(slide, "nano-heading", "Jetson Nano", 820, 244, 560, 40, { size: 27, bold: true, color: colors.ink });
  shape(slide, "nano-app", "roundRect", 825, 312, 364, 126, "#E4ECE1", colors.green, 2);
  text(slide, "nano-app-label", "上位机\nJetPack 4.x / L4T 32.x", 850, 331, 314, 84, { size: 20, bold: true, color: colors.greenDark, align: "center" });
  shape(slide, "nano-serial", "roundRect", 825, 492, 364, 126, "#F0E7D8", colors.amber, 2);
  text(slide, "nano-serial-label", "真实控制板\n串口 + 设备动作", 850, 510, 314, 85, { size: 21, bold: true, color: colors.ink, align: "center" });
  shape(slide, "nano-connection", "rect", 1004, 438, 3, 54, colors.amber);
  text(slide, "nano-connection-label", "串口", 1020, 447, 96, 28, { size: 16, color: colors.muted });
  shape(slide, "deployment-divider", "rect", 708, 248, 2, 420, colors.line);
  text(slide, "deployment-note", "同一套识别与状态机；Docker 摄像头经宿主桥接入，Nano 通过串口连接真实控制板。", 112, 723, 1370, 42, { size: 24, bold: true, color: colors.ink });
  note(slide, "约 25 秒：普通电脑由 Docker Compose 启动 PyQt 应用和 TCP 模拟器，通过容器网络连接；演示浏览器访问 noVNC。Jetson Nano 配置使用 JetPack 4.x 镜像并走串口，摄像头或串口设备需映射到容器。\n\nPC 模拟器不能替代真实控制板验收；Nano 部署还要在目标硬件上验证 GPU、摄像头、串口和固件协议。");
}

// 8. Verification and limitations
{
  const slide = baseSlide("测试证据与现场验收边界", "07  验证", 8);
  const entries = [
    ["23", "项公开单元测试通过", colors.green],
    ["30", "轮整段重播，11,880 帧读完", colors.blue],
    ["ACK", "序号匹配后才进入执行完成", colors.amber],
    ["640×480", "宿主摄像头桥实际帧", colors.rust],
  ];
  for (let index = 0; index < entries.length; index += 1) {
    const [value, caption, color] = entries[index];
    const x = 98 + index * 365;
    shape(slide, `evidence-rule-${index}`, "rect", x, 255, 6, 108, color);
    text(slide, `evidence-value-${index}`, value, x + 25, 258, 260, 62, { size: 43, bold: true, color });
    text(slide, `evidence-caption-${index}`, caption, x + 26, 325, 285, 42, { size: 18, color: colors.inkSoft });
  }
  shape(slide, "limits-rule", "rect", 98, 440, 1385, 2, colors.line);
  text(slide, "limits-title", "已知边界与现场核验", 98, 478, 390, 40, { size: 26, bold: true, color: colors.ink });
  bullet(slide, "limit-camera", "模型域外误检", "提供权重在人物和复杂室内场景可能误报，输入链路本身已实测。", 98, 548, 415, colors.green);
  bullet(slide, "limit-hardware", "真实控制板", "仍需核验串口参数、序号去重、满载信号和机械动作。", 558, 548, 440, colors.blue);
  bullet(slide, "limit-defense", "网页交互", "摄像头桥、背景音乐和宿主媒体目录已实测。", 1040, 548, 440, colors.amber);
  text(slide, "ai-disclosure", "AI 是实现辅助；现场说明以实际理解和验证为准。", 184, 752, 1210, 34, { size: 23, bold: true, color: colors.ink });
  note(slide, "约 25 秒：公开测试覆盖协议、检测适配、状态机和两个视频文件的读帧、跳转、重播。自动化回归完整读取 5 轮；本机压力回放用同一个 VideoCapture 连续完整解码 30 轮，每轮 396 帧，共 11,880 帧，约 23 秒，没有读帧失败。这验证视频解码资源复用，不等同 YOLO 推理性能或长时间内存测量。\n\n真实演示必须对齐硬件验收：摄像头和推理速度、串口实际参数、控制板去重和机械动作。Docker/TCP 模拟的成功不等于真实硬件通过。最后如实说明 AI 帮助了哪些工作，并现场讲解自己掌握的实现。");
}

presentation.slides.items[1].speakerNotes.text =
  "约 25 秒。视频由 OpenCV 逐帧读取。Docker 中的摄像头由宿主桥采集为 JPEG 流，经 host.docker.internal 进入容器，再走同一套 YOLO、状态机和通信链路。PyQt 工作台通过 noVNC 显示在浏览器中。";
presentation.slides.items[5].speakerNotes.text =
  "约 30 秒。新版工作台采用蓝白花卉界面，郊野开场、返回郊野、视频控制、摄像头桥、背景音乐、分类统计、通信日志和退出功能全部保留。耗时处理仍在 QThread 中运行，浏览器只负责显示。";
presentation.slides.items[6].speakerNotes.text =
  "约 25 秒。普通电脑使用 Docker Compose 启动应用和 TCP 模拟下位机，浏览器通过 noVNC 访问。Windows 摄像头经本机桥接入容器，宿主视频可放入 media 文件夹后选择。Jetson Nano 通过串口连接真实控制板。";
presentation.slides.items[7].speakerNotes.text =
  "约 25 秒。23 项单元测试通过，视频重播压力测试完成 30 轮，共 11880 帧。网页摄像头桥、背景音乐和宿主媒体目录已实测。已知边界是提供权重在人物和复杂室内场景可能出现域外误检，真实控制板和串口动作仍需在硬件上核验。";

for (let index = 0; index < presentation.slides.items.length; index += 1) {
  const slide = presentation.slides.items[index];
  const preview = await presentation.export({ slide, format: "png", scale: 1 });
  const pngPath = path.join(buildDir, `slide-${String(index + 1).padStart(2, "0")}.png`);
  await fs.writeFile(pngPath, new Uint8Array(await preview.arrayBuffer()));
  const layout = await slide.export({ format: "layout" });
  await fs.writeFile(path.join(buildDir, `slide-${String(index + 1).padStart(2, "0")}.layout.json`), await layout.text());
}

const draft = await PresentationFile.exportPptx(presentation);
await draft.save(draftPath);

const { finalizePresentation } = await import(pathToFileURL(path.join(skillDir, "container_tools/artifact_tool_utils.mjs")).href);
await fs.rm(finalPath, { force: true });
await fs.rm(path.join(validationDir, "smart-waste-sorting-validation-current.json"), { force: true });
const finalization = await finalizePresentation({
  explicitTotalSlideCount: 8,
  workspaceDir,
  candidatePath: draftPath,
  finalPath,
  pythonExecutable: "C:/Users/17795/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe",
  integrityValidatorPath: path.join(skillDir, "container_tools/inspect_presentation_package_integrity.py"),
  layoutValidatorPath: path.join(skillDir, "container_tools/inspect_presentation_layout_geometry.py"),
  layoutArgs: ["--expected-slide-size-emu", "15240000,8572500", "--validate-bullet-geometry", "--validate-heading-fit"],
  requiredNativeTableOwnerSlides: [],
  requiredNativeChartOwnerSlides: [],
  fontPolicy: { basis: "design", families: [font] },
  verifyArtifactToolImport: true,
  receiptPath: path.join(validationDir, "smart-waste-sorting-validation-current.json"),
});

await fs.copyFile(finalPath, publishedPath);
console.log(JSON.stringify({ finalPath, publishedPath, pdfPath, slides: presentation.slides.items.length, finalization }, null, 2));
process.exit(0);
