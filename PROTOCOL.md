# 上下位机通信协议

## 数据帧

| 字段 | 长度 | 说明 |
|---|---:|---|
| 帧头 | 2 | 固定 `AA 55` |
| LENGTH | 1 | `COMMAND + PAYLOAD` 的字节数，范围 1～64 |
| COMMAND | 1 | 命令字 |
| PAYLOAD | N | 命令参数 |
| CHECKSUM | 1 | 从 LENGTH 到 PAYLOAD 的累加和低 8 位 |

垃圾分类请求示例：序号为 `0x11`，可回收垃圾为 `0x03`。

```text
AA 55 03 01 11 03 18
```

其中校验和为：

```text
(03 + 01 + 11 + 03) & FF = 18
```

## 命令

| 命令 | 数值 | 载荷 |
|---|---:|---|
| WASTE_RESULT | `01` | `SEQUENCE, WASTE_TYPE` |
| ACK | `02` | `ORIGINAL_COMMAND, SEQUENCE` |
| ACTION_DONE | `03` | `SEQUENCE` |
| BIN_FULL | `04` | `WASTE_TYPE` |
| START_COMPRESS | `05` | `SEQUENCE` |
| HEARTBEAT | `06` | 可为空 |
| ERROR | `7F` | UTF-8 错误文本 |

## 垃圾类型

| 类型 | 数值 |
|---|---:|
| 有害垃圾 | `01` |
| 其他垃圾 | `02` |
| 可回收垃圾 | `03` |
| 厨余垃圾 | `04` |

## 序号与重发

上位机每次产生新动作时递增八位序号。超时重发必须使用原序号。下位机如果再次
收到已经执行完成的 `(COMMAND, SEQUENCE)`，只回复 ACK 和 ACTION_DONE，不能重复
执行机械动作或重复计数。

解析器必须支持：

- 一个数据帧被拆成任意数量的 TCP/串口片段。
- 一次读取包含多个完整数据帧。
- 帧前存在噪声字节。
- 校验错误后能够找到下一个合法帧。
