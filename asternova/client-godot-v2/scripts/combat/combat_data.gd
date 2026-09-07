class_name CombatData
extends Resource

## M2 战斗与高机动身法核心参数表（基于 /grill-me 严格对齐成果）

@export_group("基础移动 (Locomotion)")
@export var walk_speed: float = 2.8 ## 动捕 walk 剪辑标定移速（优雅快步）
@export var sprint_speed: float = 7.0 ## 动捕 run 剪辑标定移速（疾跑）
@export var acceleration: float = 24.0
@export var friction: float = 20.0
@export var air_control: float = 0.65
@export var base_gravity: float = 20.0
@export var fall_gravity_multiplier: float = 1.8 ## 下落重力加倍，避免轻飘漂浮感

@export_group("贴地滑铲 (Slide)")
@export var slide_initial_speed: float = 12.0 ## 滑铲爆发初速度
@export var slide_duration: float = 0.85 ## 平地最大滑行时长(秒)
@export var slide_friction: float = 6.0 ## 滑铲阻尼
@export var slide_slope_acceleration: float = 18.0 ## 下坡重力加速加成
@export var slide_jump_momentum_keep: float = 0.90 ## 滑铲跳动量保留率(90%)
@export var slide_height: float = 0.85 ## 滑铲时碰撞体高度

@export_group("立体机动 (Vertical Mobility)")
@export var jump_velocity_1: float = 8.8 ## 一段跳速度 (对应高度约 3.2m)
@export var jump_velocity_2: float = 7.8 ## 二段跳速度 (对应额外升高约 2.5m)
@export var wall_jump_up_speed: float = 7.5 ## 蹬墙向上速度
@export var wall_jump_out_speed: float = 8.5 ## 蹬墙向外推开速度
@export var max_wall_jumps: int = 3 ## 连续蹬墙跳上限次数
@export var plunge_speed: float = 24.0 ## 空中「星坠断空」垂直下砸极速
@export var plunge_impact_radius: float = 4.5 ## 落地冲击波击退半径

@export_group("极限闪避 (Dash & Perfect Dodge)")
@export var dash_speed: float = 20.0 ## 0.25s 冲出 5m 的爆发速度
@export var dash_duration: float = 0.25 ## 闪避时长
@export var dash_cooldown: float = 0.55 ## 闪避冷却
@export var dash_iframe_duration: float = 0.16 ## 瞬时无敌帧时间
@export var perfect_dodge_window: float = 0.12 ## 受击判定前完美极闪窗口
@export var time_dilation_factor: float = 0.25 ## 极闪周围时停减速倍率
@export var time_dilation_duration: float = 0.50 ## 时停减速持续时长(秒)

@export_group("四段流光刀术 (Combo Attack)")
@export var input_buffer_time: float = 0.18 ## 输入缓冲缓存时长(不吞键)
@export var combo_timeout: float = 1.1 ## 连段重置重试窗口
@export var soft_lock_distance: float = 4.5 ## 准星前向软吸附索敌最大距离
@export var soft_lock_pull_speed: float = 8.0 ## 软吸附微滑步推力
@export var combo_damage: Array[float] = [25.0, 30.0, 45.0, 75.0]
@export var combo_lunge_speed: Array[float] = [3.5, 3.0, 6.0, 8.5] ## 每段出刀前冲推力
## 四段连招对应的动捕剪辑真实时长（Slash1/Slash2/Slash3/SlashUppercut，来自 aster_animlib）
@export var combo_anim_lengths: Array[float] = [1.167, 1.167, 1.792, 1.375]

@export_group("近身索敌吸附 (Magnetic Lunge)")
@export var magnetic_lunge_distance: float = 0.4 ## 挥刀时自动向目标平滑前突距离(米)
@export var magnetic_lunge_cone_deg: float = 45.0 ## 角色前方扇形吸附判定半角(度)
@export var magnetic_lunge_windup: float = 0.12 ## 前突加速窗口时长(秒,对齐出刀前摇)
@export var magnetic_lunge_stop_margin: float = 1.1 ## 距目标近于此距离则不再前突(防顶脸穿模)

@export_group("纳刀架刀与居合蓄力 (Guard & Iaijutsu)")
@export var parry_window: float = 0.15 ## 架刀前 0.15s 完美弹刀判定窗口
@export var charge_tier_1_time: float = 0.40 ## 1阶轻拔刀耗时
@export var charge_tier_2_time: float = 0.90 ## 2阶苍蓝星月斩耗时
@export var charge_tier_3_time: float = 1.50 ## 3阶金芒次元穿透斩耗时
@export var charge_dash_distances: Array[float] = [3.0, 6.0, 10.0] ## 各阶居合突进距离
@export var charge_damages: Array[float] = [50.0, 110.0, 220.0]
@export var iai_release_length: float = 1.333 ## 拔刀释放动捕剪辑时长（SlashRelease）
@export var parry_length: float = 0.5 ## 完美弹刀动捕剪辑时长（GuardParry）

@export_group("运镜与打击感 (Camera & Feedback)")
@export var camera_tpp_distance: float = 2.8 ## 第三人称基准臂长
@export var camera_tpp_offset: Vector3 = Vector3(0.45, 1.35, 0.0) ## 越肩偏置
@export var camera_fpp_offset: Vector3 = Vector3(0.0, 1.45, -0.15) ## 第一人称视线位置
@export var fov_base: float = 75.0
@export var fov_max: float = 88.0 ## 极速滑铲与居合冲刺时最大 FOV

@export_group("单体局部卡肉与受击反馈 (Local Hitstop & Hit Feedback)")
@export var hitstop_stage_freeze: Array[float] = [0.04, 0.04, 0.03, 0.10] ## 各段普攻命中单体冻结时长(秒)
@export var hitstop_stage2_second: float = 0.06 ## 3段双穿刺第二段微卡肉时长(秒)
@export var hitstop_stage2_gap: float = 0.09 ## 3段双刺两次卡肉的间隔(秒)
@export var hitstop_iaijutsu: float = 0.15 ## 居合穿透斩重卡肉时长(秒)
@export var hit_trauma_stage: Array[float] = [0.15, 0.15, 0.15, 0.65] ## 各段命中镜头震动量(4段终结大震屏)
@export var hit_trauma_iaijutsu: float = 0.5 ## 居合穿透斩镜头震动量
@export var finisher_knock_distance: float = 0.45 ## 4段终结木桩击退后仰距离(米)
@export var hit_flash_duration: float = 0.06 ## 受击漫反射闪白时长(秒)
@export var iai_flash_duration: float = 0.06 ## 居合全屏闪白时长(秒)
@export var trauma_decay: float = 2.2 ## 震屏能量衰减速度
