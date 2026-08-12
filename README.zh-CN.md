# INDEVOLT Home Assistant 集成

用于监控和控制 [INDEVOLT](https://www.indevolt.com/) 设备的 Home Assistant
自定义集成。

英文版：[README.md](README.md) · [变更日志](CHANGE.zh-CN.md)

## 使用前提

- [ ] 已按照 [Home Assistant 官方安装指南](https://www.home-assistant.io/installation/)
  完成安装。
- [ ] INDEVOLT 设备与 Home Assistant 服务器位于**同一局域网**。
- [ ] INDEVOLT 设备已通电并取得 **IP 地址**。
  - 可在路由器管理列表中查询；
  - 也可在 INDEVOLT App 的设备设置中查看。
- [ ] 已开启 INDEVOLT 设备的 **API 功能**。本集成仅支持 OpenData HTTP 模式。

<img width="800" alt="3http_mode" src="https://github.com/user-attachments/assets/67f8ed96-abb8-4368-b3f3-b2a3484bd4b9" />

- [ ] 确认固件版本满足最低要求。

  | 设备型号 | 最低固件版本 |
  | --- | --- |
  | BK1600/BK1600Ultra | V1.3.0A_R006.072_M4848_00000039 |
  | SolidFlex2000/PowerFlex2000 | CMS: V1406.07.002E |

<img width="400" alt="4fw_version" src="https://github.com/user-attachments/assets/7fb6d58f-9c95-4945-b588-810e68481f5b" />

## 使用 HACS 安装

本仓库通过 HACS 自定义仓库方式安装：

1. 在 Home Assistant 中打开 HACS。
2. 打开右上角菜单，选择 **Custom repositories**。
3. 输入 `https://github.com/INDEVOLT/homeassistant-indevolt`，类型选择
   **Integration**，然后点击 **ADD**。
4. 在 HACS 中打开 **INDEVOLT**，点击 **Download**。
5. 重启 Home Assistant。
6. 进入 **Settings** > **Devices & services**，添加 INDEVOLT。

如果当前已经有另一套同域实现创建的 Indevolt 条目，请先阅读
[在同域实现之间切换](#在同域实现之间切换)，再安装本仓库。

HACS 与下方手工方式都会安装到同一个 `custom_components/indevolt` 目录，
不要混用两种方式安装的文件。

## 手工安装

### 步骤 1：下载仓库

1. 点击 **Code** > **Download ZIP**。
2. 将 ZIP 文件解压到电脑中。

### 步骤 2：找到 Home Assistant 配置目录

- **Home Assistant OS**：配置目录为 `/config`。
- **Home Assistant Container**：找到 `configuration.yaml` 文件所在的目录，
  该目录即为配置目录。

**提示**：配置目录中应包含 `configuration.yaml` 文件。

```text
配置目录/
└── configuration.yaml
```

### 步骤 3：创建自定义集成目录

1. 进入配置目录。
2. 如果 `custom_components` 目录不存在，请创建该目录。

```text
配置目录/
├── custom_components/
└── configuration.yaml
```

**注意**：所有自定义集成都必须放在 `custom_components` 目录中，否则
Home Assistant 无法识别。

### 步骤 4：添加集成文件

1. 在解压后的仓库中找到 `custom_components/indevolt`。
2. 将完整的 `indevolt` 目录复制到 Home Assistant 的 `custom_components`
   目录中。不要与其他版本的文件混合。

安装位置示例（`indevolt` 内部文件以下载的版本为准）：

```text
配置目录/
└── custom_components/
    └── indevolt/
        ├── __init__.py
        ├── manifest.json
        └── ...
```

### 步骤 5：重启 Home Assistant

1. 在网页界面中选择 **Settings** > **System**。
2. 点击右上角的重启图标。
3. 点击 **Restart Home Assistant**。
4. 点击 **RESTART**。

<img width="1000" alt="5restart_ha" src="https://github.com/user-attachments/assets/1270a590-faf8-43a4-8989-27923d1f3887" />

### 步骤 6：在 Home Assistant 中添加集成

1. 重启后进入网页界面，选择 **Settings** > **Devices & services**。

   <img width="800" alt="" src="https://github.com/user-attachments/assets/f19c8fba-7eec-4994-8fed-4b5a7b2b2d3b" />

2. 点击右下角的 **+ADD INTEGRATION**。

   <img width="150" alt="image" src="https://github.com/user-attachments/assets/9282240e-f408-4ab0-a2ca-e6701994eaee" />

3. 搜索并选择 INDEVOLT 集成。

   <img width="400" alt="" src="https://github.com/user-attachments/assets/836a3d34-d2ad-44c0-87f2-79fc80acd52d" />

4. 填写配置参数：
   - `host`：设备 IP 地址，可通过路由器或 INDEVOLT App 查询。
   - `scan_interval`：数据更新间隔，默认值为 30 秒。

     <img width="300" alt="" src="https://github.com/user-attachments/assets/0a0d38ed-15ed-4072-98bf-c94920d362cb" />

5. 点击 **SUBMIT** 完成安装。
6. 按照 Home Assistant 界面提示完成设置。

   <img width="300" alt="image" src="https://github.com/user-attachments/assets/f316fa13-44e4-4325-b3a8-09b904b0bd6f" />

## 查看集成

选择 INDEVOLT 集成，即可查看设备和实体信息。

<img width="300" alt="" src="https://github.com/user-attachments/assets/3997f4c9-c146-4c87-9d48-c0970dbe833c" />

<img width="800" alt="" src="https://github.com/user-attachments/assets/c26f0a2c-70ae-456b-9c66-683c2cb52617" />

## 更新集成

### 使用 HACS 更新

1. 更新前创建 Home Assistant 备份。
2. 从 **Settings** > **Updates** 安装更新，或者在 HACS 中打开 INDEVOLT，
   选择 **Redownload**。
3. 重启 Home Assistant。
4. 确认原有 INDEVOLT 条目、设备和实体仍能正常加载。

需要回退时，请打开 **Redownload**；如果 HACS 提供版本选择器，请选择较早
版本。如果没有可选的旧版本，请恢复完整的 `custom_components/indevolt`
目录备份，或者手工重新安装所需的仓库版本。随后重启 Home Assistant。

### 手工更新

1. 将现有 `custom_components/indevolt` 目录完整备份到
   `custom_components` 之外，并记录当前安装的版本。
2. 下载新版本，使用该版本完整的 `custom_components/indevolt`
   目录替换已安装的 `indevolt` 目录。不要合并不同版本的文件。
3. 保留现有 INDEVOLT 集成条目、设备和实体。本次更新不需要删除后重新添加集成。
4. 重启 Home Assistant。
5. 确认 INDEVOLT 加载时没有相关错误，并确认原有集成条目、设备和实体仍然存在。

### 回退手工更新

如果验证失败，请使用完整备份替换 `custom_components/indevolt` 目录，重启
Home Assistant，并确认原有集成条目、设备和实体能够正常加载。

### 在同域实现之间切换

从 HACS 移除本仓库，或者删除 `custom_components/indevolt`，都不会删除已经
保存的集成条目，也不会把该条目自动转换给 Home Assistant 中已经有的 Indevolt
集成。两套实现虽然使用相同 domain，但保存的配置数据不同。

无论向哪个方向切换，都应当：

1. 创建 Home Assistant 备份。
2. 记录受影响的设备、实体 ID、仪表盘、脚本和自动化引用。
3. 删除当前 Indevolt 集成条目，切换已安装代码，重启 Home Assistant，然后
   使用目标实现重新添加 Indevolt。
4. 核对重新创建的实体；如引用发生变化，修复后再恢复自动化运行。

## 创建自动化：设置实时控制

1. 进入 **Settings** > **Automations & scenes**。

   <img width="800" alt="" src="https://github.com/user-attachments/assets/b5bb0b3a-9fce-49ae-b0ce-c9637e69cf9d" />

2. 点击右下角的 **+ Create automation**。

   <img width="800" alt="" src="https://github.com/user-attachments/assets/6c3ed052-eba3-4ae1-b344-4b3c4004eb80" />

3. 选择 **Create new automation**。

   <img width="300" alt="image" src="https://github.com/user-attachments/assets/0dd42045-2eeb-4750-b4a6-d8ada2289b0b" />

4. 点击 **+ Add Trigger**，按需要设置触发条件。

   <img width="500" alt="image" src="https://github.com/user-attachments/assets/2988715f-c0ae-4bac-964e-7d483540120f" />

5. 点击 **+ Add Action**，配置设备操作。
6. 根据目标型号选择 Action：
   - **Set SolidFlex2000/PowerFlex2000 Work Mode**；或
   - **Set BK1600/BK1600 Ultra Work Mode**。

   下方截图以 SolidFlex2000/PowerFlex2000 为例。

   <img width="300" alt="image" src="https://github.com/user-attachments/assets/9b03b0f5-ecbd-43eb-a1f1-e3b82019724f" />

7. 在 **Target** 区域点击 **+ Choose Device**，从列表中选择设备。

   <img width="800" alt="" src="https://github.com/user-attachments/assets/91964bf7-454e-48b3-9064-badb18706489" />

   <img width="300" alt="image" src="https://github.com/user-attachments/assets/6a7b6638-5be3-4749-aed2-f088a73d8fd4" />

8. 在 **Work Mode** 区域选择 **Real-Time Control**，然后按需要设置
   **Status**、**Power** 和 **Target SOC**。

   <img width="300" alt="image" src="https://github.com/user-attachments/assets/bedb1966-513f-4246-b7c4-5f5c579a2e3f" />

   <img width="300" alt="image" src="https://github.com/user-attachments/assets/a6ffeff5-e5c7-45a4-8aa5-5a948ce04b36" />

9. 点击 **Save** 完成自动化设置。

## 常见问题

| 问题描述 | 解决方法 |
| --- | --- |
| 搜索列表中找不到集成 | 确认集成文件位于正确目录：`custom_components/indevolt`。 |
| 在两套实现之间切换后，集成无法加载 | 同域配置条目不会自动转换。请恢复原来的代码，或者删除现有条目，再使用需要的实现重新添加 Indevolt。 |
| - 无法添加设备<br>- 无法连接设备<br>- 没有可用数据 | 这通常是由 **HTTP 请求失败** 导致的。<br>1. 确认设备已通电。<br>2. 确认设备 IP 地址正确。<br>3. 在 INDEVOLT App 中检查设备网络状态。<br>4. 确认已满足全部[使用前提](#使用前提)。 |

如果仍然遇到问题，请查看 **Home Assistant 日志**中的详细错误信息。

## 参与贡献

欢迎提供反馈和贡献！你可以提交 Issue 分享建议，也可以提交 Pull Request。
