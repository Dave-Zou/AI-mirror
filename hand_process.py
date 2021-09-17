# 加载QT界面和多线程
import time

import qt05_webview03 as qt_main
from multiprocessing import Process, Lock, Manager, Queue
import numpy as np


class hand:
    def __init__(self):
        # 创建锁和共享对象
        self.lock = Lock()
        self.q = Queue()

        # 传入锁和共享对象，开启qt进程
        t1 = Process(target=qt_main.runWindow, args=(self.lock, self.q))
        t1.start()
        print('Qt进程已开启，继续。。。。。。')

        # 摄像头显示大小
        self.capSize = (640, 480)
        # Qt显示大小
        self.windowSize = (1920, 1080)

        # 状态代号
        self.state = 'normal'
        self.state_init(1)
        self.state_init(2)
        self.state_init(3)

    '''
        改变大小
    '''

    def changeBallSize(self, angle_list):
        if angle_list is None:
            return

        angle = np.mean(angle_list[1:])  # 手指角度均值
        # print(angle)
        info = {'isChange': True, 'name': 'Size', 'value': 1000 - angle * 5.5}
        self.q.put(info)

    '''
        移动位置
    '''

    def changeBallPosition(self, plam_center):
        if plam_center is None:
            return
        # 获取显示位置
        x = plam_center[0]
        y = plam_center[1]
        print(x, y)
        # 等比例映射到Qt界面的位置
        x = 100 + x * ((self.windowSize[0] - 200) / self.capSize[0])
        y = 100 + y * ((self.windowSize[1] - 200) / self.capSize[1])
        print(x, y)

        # 存入队列
        info = {'isChange': True, 'name': 'Pos', 'value': [x, y]}
        self.q.put(info)

    def main(self, handpose_list, gesture_list, hands_angle_list):
        # print(handpose_list, gesture_list)
        # print(bbox)
        # -------------------------------------

        # --------------------------------------
        self.update_state(handpose_list, gesture_list, hands_angle_list)

    def get_hand_size(self, hand):
        each_hand_points = hand[0]
        x_points_list = np.asarray([d['x'] for d in each_hand_points.values()])
        y_points_list = np.asarray([d['y'] for d in each_hand_points.values()])
        # # X缩放到100
        # Max_x = bbox[i][2] - bbox[i][0]
        # sc = 200 / Max_x
        # x_points_list = x_points_list * sc
        # y_points_list = y_points_list * sc
        # 平均值
        average_x = np.mean(x_points_list)
        average_y = np.mean(y_points_list)
        # 方差
        var_x = np.var(x_points_list)
        var_y = np.var(y_points_list)
        # # 方差矢量和（X方向权重减少）
        # var_xy = (var_x**2 * 0.3 + var_y**2 * 0.7) / 2
        # 总体标准差
        std_x = var_x / 21
        std_y = var_y / 21
        # 标准差矢量和（X方向的权重减少）
        std_xy = ((std_x * 0.3) ** 2 + (std_y * 0.7) ** 2) ** 0.5

        # 标准差代表手势关键点的离散程度，值越小，说明手里摄像头较远，或者手指的弯曲程度越大
        # print('中心: ', average_x, average_y)
        # print('标准差: ', std_xy)
        # 以标准差作为手的大小
        return std_xy

    def update_pro_rate(self, p):
        info = {'isChange': True, 'name': 'pro_rate'}
        if p == 1:
            rate = self.interactive_1_recharge_power / self.interactive_1_recharge_power_threshold * 100
            rate = np.around(rate, 2)
            info['value'] = ('interactive_1', rate)
            self.q.put(info)

        if p == 2:
            rate = self.interactive_2_recharge_power / self.interactive_2_recharge_power_threshold * 100
            rate = np.around(rate, 2)
            info['value'] = ('interactive_2', rate)
            self.q.put(info)

    # noinspection PyAttributeOutsideInit
    def state_init(self, state_num):
        # 正常状态 -> 交互状态1
        if state_num == 1:
            self.interactive_1_x_range = (100, 400)
            self.interactive_1_y_range = (200, 400)
            self.interactive_1_size_threshold = 40

            self.interactive_1_recharge_hand_id = -1
            self.interactive_1_recharge_hand_id_alive = False
            self.interactive_1_ID_disappear_time = None
            self.interactive_1_ID_disappear_time_threshold = 0.5
            self.interactive_1_ID_disappear_info = {}
            self.interactive_1_recharge_signal = False
            self.interactive_1_recharge_power = 0
            self.interactive_1_recharge_power_threshold = 50
            self.interactive_1_recharge_time = 0
            self.interactive_1_recharge_complete = False
            self.interactive_1_recharge_complete_time = 0
            self.interactive_1_recharge_id_info = {'size': 0, 'center': (0, 0)}

        # 交互状态1 -> 交互状态2
        elif state_num == 2:
            self.interactive_2_x_range = (100, 400)
            self.interactive_2_y_range = (200, 400)
            self.interactive_2_size_threshold = 20

            self.interactive_2_start_time = time.time()
            self.interactive_2_recharge_hand_id = -1
            self.interactive_2_recharge_hand_id_alive = False
            self.interactive_2_ID_disappear_time = None
            self.interactive_2_ID_disappear_time_threshold = 0.5
            self.interactive_2_ID_disappear_info = {}
            self.interactive_2_recharge_signal = False
            self.interactive_2_recharge_power = 0
            self.interactive_2_recharge_power_threshold = 30
            self.interactive_2_recharge_time = 0
            self.interactive_2_recharge_complete = False
            self.interactive_2_recharge_complete_time = 0
            self.interactive_2_recharge_id_info = {'size': 0, 'center': (0, 0)}

        elif state_num == 3:
            self.interactive_3_x_range = (20, 620)
            self.interactive_3_y_range = (20, 460)
            self.interactive_3_size_threshold = 30
            self.interactive_3_control_size_hand_id = -1
            self.interactive_3_control_position_hand_id = -1
            self.interactive_3_control_position_hand_id_alive = False
            self.interactive_3_control_size_hand_id_alive = False

    def update_state(self, handpose_list, gesture_list, hands_angle_list):
        print('update state!', end='')
        hand_id_list = [h[3]['id'] for h in handpose_list]
        click_state_list = [h[3]['click'] for h in handpose_list]

        # * ---------------------------------------------------------------------------------------------------------------
        # * interactive_1
        # 是否处于充能状态
        if self.interactive_1_recharge_signal:
            # 充能ID处于存活状态
            if self.interactive_1_recharge_hand_id_alive:
                # 如果ID不存在当前帧中，则表明该ID已消失
                if self.interactive_1_recharge_hand_id not in hand_id_list:
                    print('原ID已消失')
                    self.interactive_1_recharge_hand_id_alive = False  # 取消存活标志
                    self.interactive_1_ID_disappear_time = time.time()  # 更新消失时间
                    self.interactive_1_ID_disappear_info = self.interactive_1_recharge_id_info  # 更新消失时刻ID的信息
            # 充能ID已不存活
            else:
                # 确定已消失时间，超过阈值，则重置状态
                if time.time() - self.interactive_1_ID_disappear_time >= self.interactive_1_ID_disappear_time_threshold:
                    # 超过可消失重置的时间阈值，将重置状态
                    self.state_init(1)
                    print('已重置状态')
                    self.update_pro_rate(1)
        # * ---------------------------------------------------------------------------------------------------------------

        # * ---------------------------------------------------------------------------------------------------------------
        # * interactive_2
        # 是否处于充能状态
        if self.interactive_2_recharge_signal:
            # 充能ID处于存活状态
            if self.interactive_2_recharge_hand_id_alive:
                # 如果ID不存在当前帧中，则表明该ID已消失
                if self.interactive_2_recharge_hand_id not in hand_id_list:
                    print('原ID已消失')
                    self.interactive_2_recharge_hand_id_alive = False  # 取消存活标志
                    self.interactive_2_ID_disappear_time = time.time()  # 更新消失时间
                    self.interactive_2_ID_disappear_info = self.interactive_2_recharge_id_info  # 更新消失时刻ID的信息
            # 充能ID已不存活
            else:
                # 确定已消失时间，超过阈值，则重置状态
                if time.time() - self.interactive_2_ID_disappear_time >= self.interactive_2_ID_disappear_time_threshold:
                    # 超过可消失重置的时间阈值，将重置状态
                    self.state_init(2)
                    print('已重置状态')
                    self.update_pro_rate(2)
        # * ---------------------------------------------------------------------------------------------------------------

        for i, hand in enumerate(handpose_list):
            if self.state == 'normal':
                # 当前是正常状态，非交互状态，那么当手移到屏幕中间时，开始下一状态(interactive_1)充能2s
                # 条件：手掌中心处于预定范围内，且手的大小超过阈值，手势动作为five，不能有其他动作，开始充能
                # 充能：如果当前帧满足条件，充能数增加，否则充能数减少，充能数如果小于初始值，则重置信号
                # ID： 如果在判定中ID消失，记录下消失时刻之前的大小和位置，如果在0.5s内产生满足条件的新ID，
                #      且大小和位置与前ID偏差较小，则更新ID。期间充能暂停。否则，重置状态。

                # x_range: 中心位置的X范围
                # y_range: 中心位置的Y范围
                # size_threshold: 手的大小阈值
                # recharge_hand_id: 准备交互的手的ID
                # recharge_hand_id_alive: 当前充能的ID是否存活
                # ID_disappear_time: ID消失时刻的时间
                # ID_disappear_info: 消失时刻的信息，大小和位置
                # ID_disappear_time_threshold： 消失重置的时间阈值
                # recharge_signal: 开始充能的信号
                # recharge_power: 充能计数
                # recharge_power_threshold: 充能计数阈值
                # recharge_time: 开始充能的时间
                # recharge_complete: 充能完成标志
                # recharge_complete_time: 充能完成时间
                # recharge_id_info: ID充能时的信息，大小和位置

                self.update_pro_rate(1)

                hand_id = hand_id_list[i]  # 手的ID
                hand_plam_center = hand[2]  # 手的掌心坐标
                hand_size = self.get_hand_size(hand)  # 手的大小

                # 条件判断
                condition = False
                if self.interactive_1_x_range[0] <= hand_plam_center[0] <= self.interactive_1_x_range[1]:
                    if self.interactive_1_y_range[0] <= hand_plam_center[1] <= self.interactive_1_y_range[1]:
                        if hand_size >= self.interactive_1_size_threshold and click_state_list[i] == False and \
                                gesture_list[i] == 'five':
                            condition = True  # 满足条件

                if condition:
                    print('满足条件')
                    # 满足 interactive_1 的条件
                    # 是否处于充能
                    if not self.interactive_1_recharge_signal:  # * 未处于充能状态
                        # 更新ID
                        self.interactive_1_recharge_hand_id = hand_id
                        self.interactive_1_recharge_hand_id_alive = True
                        # 发出充能信号
                        self.interactive_1_recharge_signal = True
                        # 重置开始充能的时间
                        self.interactive_1_recharge_time = time.time()

                    else:  # * 正处于充能状态
                        # 比较ID是否是当前充能的ID
                        if hand_id == self.interactive_1_recharge_hand_id:  # 是充能ID，则ID肯定存活
                            # ID充能判断
                            if self.interactive_1_recharge_power >= self.interactive_1_recharge_power_threshold:  # ! 充能完成
                                # ! 初始化此状态的所有参数
                                self.state_init(1)
                                self.state_init(2) # ! 初始化下一状态
                                # ! 进入下一状态(交互判断第二状态) interactive_1
                                self.state = "interactive_1"
                                print('enter next state!')  # ? 打印输出
                            elif 0 <= self.interactive_1_recharge_power < self.interactive_1_recharge_power_threshold:  # 充能未完成
                                self.interactive_1_recharge_power += 1.5  # 充能
                                self.interactive_1_recharge_id_info = {'size': hand_size,
                                                                       'center': hand_plam_center}  # 更新ID充能时的信息
                                print(self.interactive_1_recharge_power)  # ? 打印输出
                        else:  # ID不是当前充能的ID
                            print('ID不是当前充能的ID')
                            # 充能ID是否存活
                            if not self.interactive_1_recharge_hand_id_alive:  # 充能ID已消失
                                # 满足条件，且原充能ID已消失
                                # 将比较大小和位置，若偏差在范围内，将更新ID
                                # 计算大小和位置偏差
                                size_deviation = np.abs(hand_size - self.interactive_1_ID_disappear_info['size'])
                                position_deviation = np.sqrt(
                                    (hand_plam_center[0] - self.interactive_1_ID_disappear_info['center'][0]) ** 2 + \
                                    (hand_plam_center[1] - self.interactive_1_ID_disappear_info['center'][1]) ** 2)
                                # ! 设置大小偏差范围为 10 ，位置范围偏差为 50
                                if size_deviation <= 10 and position_deviation <= 50:
                                    # 偏差在范围内，将更新ID状态
                                    self.interactive_1_recharge_hand_id = hand_id  # 更新ID号
                                    self.interactive_1_recharge_hand_id_alive = True  # 更新存活标志
                                    self.interactive_1_ID_disappear_info = {}  # 重置消失时刻ID的信息
                                    print('ID被更新！！！')
                else:
                    print('不满足条件')
                    # 不满足条件
                    # 是否处于充能状态
                    if self.interactive_1_recharge_signal:  # * 处于充能状态
                        # 比较ID是否是当前充能的ID
                        if hand_id == self.interactive_1_recharge_hand_id:  # 是充能ID，则ID肯定存活
                            # 不满足条件，将减少充能数
                            self.interactive_1_recharge_power -= 3
                            print(self.interactive_1_recharge_power)  # ? 打印输出
                            if self.interactive_1_recharge_power < 0:  # ! 小于初始值，重置当前状态，初始化下一状态
                                self.state_init(1)
                                self.state_init(2)

            elif self.state == 'interactive_1':
                # 当前是交互状态1，当手移到屏幕中间时，开始下一状态(interactive_2)充能2s
                # 条件：手掌中心处于预定范围内，且手的大小超过阈值，手势动作为fist，不能有其他动作，开始充能
                # 充能：如果当前帧满足条件，充能数增加，否则充能数减少，充能数如果小于初始值，则重置信号
                # ID： 如果在判定中ID消失，记录下消失时刻之前的大小和位置，如果在0.5s内产生满足条件的新ID，
                #      且大小和位置与前ID偏差较小，则更新ID。期间充能暂停。否则，重置状态。

                # x_range: 中心位置的X范围
                # y_range: 中心位置的Y范围
                # size_threshold: 手的大小阈值
                # recharge_hand_id: 准备交互的手的ID
                # recharge_hand_id_alive: 当前充能的ID是否存活
                # ID_disappear_time: ID消失时刻的时间
                # ID_disappear_info: 消失时刻的信息，大小和位置
                # ID_disappear_time_threshold： 消失重置的时间阈值
                # recharge_signal: 开始充能的信号
                # recharge_power: 充能计数
                # recharge_power_threshold: 充能计数阈值
                # recharge_time: 开始充能的时间
                # recharge_complete: 充能完成标志
                # recharge_complete_time: 充能完成时间
                # recharge_id_info: ID充能时的信息，大小和位置

                if time.time() - self.interactive_2_start_time > 10:
                    self.state_init(2)
                    self.state = 'normal'
                    self.update_pro_rate(1)
                    self.update_pro_rate(2)
                    break

                self.update_pro_rate(2)

                hand_id = hand_id_list[i]  # 手的ID
                hand_plam_center = hand[2]  # 手的掌心坐标
                hand_size = self.get_hand_size(hand)  # 手的大小

                # 条件判断
                condition = False
                if self.interactive_2_x_range[0] <= hand_plam_center[0] <= self.interactive_2_x_range[1]:
                    if self.interactive_2_y_range[0] <= hand_plam_center[1] <= self.interactive_2_y_range[1]:
                        if hand_size >= self.interactive_2_size_threshold and gesture_list[i] == 'fist':
                            condition = True  # 满足条件

                if condition:
                    print('满足条件')
                    # 满足 interactive_2 的条件
                    # 是否处于充能
                    if not self.interactive_2_recharge_signal:  # * 未处于充能状态
                        # 更新ID
                        self.interactive_2_recharge_hand_id = hand_id
                        self.interactive_2_recharge_hand_id_alive = True
                        # 发出充能信号
                        self.interactive_2_recharge_signal = True
                        # 重置开始充能的时间
                        self.interactive_2_recharge_time = time.time()

                    else:  # * 正处于充能状态
                        # 比较ID是否是当前充能的ID
                        if hand_id == self.interactive_2_recharge_hand_id:  # 是充能ID，则ID肯定存活
                            # ID充能判断
                            if self.interactive_2_recharge_power >= self.interactive_2_recharge_power_threshold:  # ! 充能完成
                                # ! 初始化此状态的所有参数
                                self.state_init(2)
                                # ! 进入下一状态(交互判断第二状态) interactive_2
                                self.state = "interactive_2"

                                print('enter next state!')  # ? 打印输出
                            elif 0 <= self.interactive_2_recharge_power < self.interactive_2_recharge_power_threshold:  # 充能未完成
                                self.interactive_2_recharge_power += 1.5  # 充能
                                self.interactive_2_recharge_id_info = {'size': hand_size,
                                                                       'center': hand_plam_center}  # 更新ID充能时的信息
                                print(self.interactive_2_recharge_power)  # ? 打印输出
                        else:  # ID不是当前充能的ID
                            print('ID不是当前充能的ID')
                            # 充能ID是否存活
                            if not self.interactive_2_recharge_hand_id_alive:  # 充能ID已消失
                                # 满足条件，且原充能ID已消失
                                # 将比较大小和位置，若偏差在范围内，将更新ID
                                # 计算大小和位置偏差
                                size_deviation = np.abs(hand_size - self.interactive_2_ID_disappear_info['size'])
                                position_deviation = np.sqrt(
                                    (hand_plam_center[0] - self.interactive_2_ID_disappear_info['center'][0]) ** 2 + \
                                    (hand_plam_center[1] - self.interactive_2_ID_disappear_info['center'][1]) ** 2)
                                # ! 设置大小偏差范围为 10 ，位置范围偏差为 30
                                if size_deviation <= 10 and position_deviation <= 50:
                                    # 偏差在范围内，将更新ID状态
                                    self.interactive_2_recharge_hand_id = hand_id  # 更新ID号
                                    self.interactive_2_recharge_hand_id_alive = True  # 更新存活标志
                                    self.interactive_2_ID_disappear_info = {}  # 重置消失时刻ID的信息
                                    print('ID被更新！！！')
                else:
                    print('不满足条件')
                    # 不满足条件
                    # 是否处于充能状态
                    if self.interactive_2_recharge_signal:  # * 处于充能状态
                        # 比较ID是否是当前充能的ID
                        if hand_id == self.interactive_2_recharge_hand_id:  # 是充能ID，则ID肯定存活
                            # 不满足条件，将减少充能数
                            self.interactive_2_recharge_power -= 3
                            print(self.interactive_2_recharge_power)  # ? 打印输出
                            if self.interactive_2_recharge_power < 0:  # ! 小于初始值，重置当前状态，初始化下一状态
                                self.state_init(2)

            elif self.state == 'interactive_2':
                # 此状态将实际产生控制信号
                # 条件：手处于一定范围内，手的大小超过预定阈值
                # ID：当有一个手满足条件时，则将其置为当前ID，此时其他ID的手无法干扰控制，
                #     当前ID消失时，若在消失重置时间阈值内，产生新ID满足大小和位置偏差，且Click状态相同，则更新
                # 控制：非Click状态时，只能控制大小，Click状态时，只能控制位置。
                # 信息：在控制时，将记录大小和位置信息到数组中，
                #      当手势更改为love时，将暂停记录，并开始确认和回退充能。充能完成之后将回退到约2s前，并保存状态。

                # x_range: 中心位置的X范围
                # y_range: 中心位置的Y范围
                # size_threshold: 手的大小阈值
                # control_size_hand_id: 正在控制大小的手的ID
                # control_position_hand_id: 正在控制位置的手的ID
                # control_hand_id_alive: 当前控制的ID是否存活
                # size_ID_disappear_time: 大小ID消失时刻的时间
                # size_ID_disappear_info: 大小ID消失时刻的信息，大小、位置、Click
                # position_ID_disappear_time: 位置ID消失时刻的时间
                # position_ID_disappear_info: 位置ID消失时刻的信息，大小、位置、Click
                # ID_disappear_time_threshold: 消失重置的时间阈值
                # control_signal: 开始控制的信号
                # control_size_signal: 开始控制大小的信号
                # control_id_info: ID控制时的信息，大小、位置、Click
                # control_id_info_size_array: 记录ID控制时的大小值，最大为50，约2s
                # control_id_info_position_array: 记录ID控制时的位置，最大为50，约2s

                hand_id = hand_id_list[i]  # 手的ID
                hand_plam_center = hand[2]  # 手的掌心坐标
                hand_size = self.get_hand_size(hand)  # 手的大小

                # 条件判断
                size_condition = False
                position_condition = False
                if self.interactive_3_x_range[0] <= hand_plam_center[0] <= self.interactive_3_x_range[1]:
                    if self.interactive_3_y_range[0] <= hand_plam_center[1] <= self.interactive_3_y_range[1]:
                        if hand_size >= self.interactive_3_size_threshold:
                            if not click_state_list[i]: # 非Click状态
                                size_condition = True  # 满足改变大小的条件
                            else: # Click状态
                                position_condition = True  # 满足改变位置的条件

                if size_condition:  # 满足控制大小的条件
                    print('size condition')
                    # 是否正在控制
                    self.changeBallSize(hands_angle_list[i])

                if position_condition:  # 满足控制位置的条件
                    print('changePos')
                    self.changeBallPosition(hand_plam_center)
