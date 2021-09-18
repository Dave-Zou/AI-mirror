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

        # Qt显示窗口大小
        self.windowSize = (1920, 1080)

        # 状态代号
        self.state = 'index page'

        # 初始化five条件充能
        self.five_recharge = self.condition_charge(recharge_gesture='five')
        self.five_recharge.size_threshold = 50

        # 初始化fist条件充能
        self.fist_recharge = self.condition_charge(recharge_gesture='fist')
        # 修改充能条件
        self.fist_recharge.need_click_state = None # 不需要判断Click
        self.fist_recharge.x_range = (140, 500)  # 缩小X范围
        self.fist_recharge.y_range = (90, 400) # 缩小Y范围
        self.fist_recharge.size_threshold = 20 # 减小充能大小阈值
        self.fist_recharge.disappear_position_deviation = 40 # 增大消失重置位置偏差


    #* 发送大小
    def changeBallSize(self, angle_list):
        if angle_list is None:
            return

        angle = np.mean(angle_list[1:])  # 手指角度均值
        # print(angle)
        info = {'isChange': True, 'name': 'Size', 'value': 1000 - angle * 5.5}
        self.q.put(info)

    #* 发送位置
    def changeBallPosition(self, palm_center):
        if palm_center is None:
            return
        # 获取显示位置
        x = palm_center[0]
        y = palm_center[1]
        print(x, y)
        # 等比例映射到Qt界面的位置
        x = 100 + x * ((self.windowSize[0] - 200) / self.capSize[0])
        y = 100 + y * ((self.windowSize[1] - 200) / self.capSize[1])
        print(x, y)

        # 存入队列
        info = {'isChange': True, 'name': 'Pos', 'value': [x, y]}
        self.q.put(info)

    def main(self, handPose_list, gesture_list, hands_angle_list):
        # 数据传入，处理中心
        self.update_state(handPose_list, gesture_list, hands_angle_list)

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

    class condition_charge:
        def __init__(self, recharge_gesture=None, isReset=False):
            '''
            手势充能的判定
            '''

            # x_range: 中心位置的X判定范围
            # y_range: 中心位置的Y判定范围
            # size_threshold: 手的大小阈值

            # recharge_hand_id: 准备交互的手的ID
            # recharge_hand_id_alive: 当前充能的ID是否存活
            # ID_disappear_time: ID消失时刻的时间
            # ID_disappear_info: 消失时刻的信息，大小和位置
            # disappear_size_deviation: 消失重置的大小偏差
            # disappear_position_deviation: 消失重置的位置偏差
            # ID_disappear_time_threshold： 消失重置的时间阈值
            # recharge_signal: 开始充能的信号
            # recharge_power: 充能计数值
            # recharge_increment_per_frame: 每帧充能增量
            # recharge_decrease_per_frame: 每帧充能减量
            # recharge_power_threshold: 充能计数阈值
            # recharge_time: 开始充能的时间
            # recharge_complete: 充能完成标志
            # recharge_complete_time: 充能完成时间
            # recharge_id_info: ID充能时的信息，大小和位置
            # recharge_gesture: 满足条件的手势名
            # need_click_state: 是否需要判断click的状态（False,True），None表示不需要
            # recharge_rate: 充能率（0-100）

            if not isReset: # 初始化，非手动重置
                # 判断常量
                self.x_range = (100, 540)
                self.y_range = (50, 440)
                self.size_threshold = 40
                self.ID_disappear_time_threshold = 0.5
                self.disappear_size_deviation = 10
                self.disappear_position_deviation = 30
                self.recharge_increment_per_frame = 2
                self.recharge_decrease_per_frame = 3
                self.recharge_power_threshold = 50
                self.need_click_state = False
                self.recharge_gesture = recharge_gesture
                self.isPrint = False # 调试输出
            # 判断变量
            self.recharge_hand_id = -1
            self.recharge_hand_id_alive = False
            self.ID_disappear_time = None
            self.ID_disappear_info = {}

            self.recharge_signal = False
            self.recharge_power = 0

            self.recharge_time = 0
            self.recharge_complete = False
            self.recharge_complete_time = 0
            self.recharge_id_info = {'size': 0, 'center': (0, 0)}

            self.recharge_rate = 0

            if isReset:
                self.debugPrint('is Reset ！！！')


        def debugPrint(self, *args, **kwargs):
            if self.isPrint:
                print(*args, **kwargs)

        def update_recharge_rate(self):
            # 更新充能率，保留两位小数
            self.recharge_rate = np.around(self.recharge_power / self.recharge_power_threshold * 100, 2)

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

        def recharge(self, handPose_list, gesture_list):
            '''
            当动作序列检测失败，将返回 'reset state'，并重置状态。
            当动作序列检测完成，将返回 'complete'， 并更新完成标志。
            '''
            if self.recharge_complete:
                # 如果已经充能完成了，就直接返回充能完成，不再继续充能判断
                return 'Recharge has been completed !!!'

            self.debugPrint('update state!', end='')
            hand_id_list = [h[3]['id'] for h in handPose_list]
            click_state_list = [h[3]['click'] for h in handPose_list]

            # * ---------------------------------------------------------------------------------------------------------------
            # * interactive
            # 是否处于充能状态
            if self.recharge_signal:
                # 充能ID处于存活状态
                if self.recharge_hand_id_alive:
                    # 如果ID不存在当前帧中，则表明该ID已消失
                    if self.recharge_hand_id not in hand_id_list:
                        self.debugPrint('原ID已消失')
                        self.recharge_hand_id_alive = False  # 取消存活标志
                        self.ID_disappear_time = time.time()  # 更新消失时间
                        self.ID_disappear_info = self.recharge_id_info  # 更新消失时刻ID的信息
                # 充能ID已不存活
                else:
                    # 确定已消失时间，超过阈值，则重置状态
                    if time.time() - self.ID_disappear_time >= self.ID_disappear_time_threshold:
                        #! 超过可消失重置的时间阈值，将重置状态
                        self.__init__(isReset=True)
                        return 'reset state'

            # * ---------------------------------------------------------------------------------------------------------------
            self.debugPrint('hands recharge')
            for i, hand in enumerate(handPose_list):
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
                #
                # ID_disappear_time_threshold： 消失重置的时间阈值
                # recharge_signal: 开始充能的信号
                # recharge_power: 充能计数
                # recharge_power_threshold: 充能计数阈值
                # recharge_time: 开始充能的时间
                # recharge_complete: 充能完成标志
                # recharge_complete_time: 充能完成时间
                # recharge_id_info: ID充能时的信息，大小和位置

                hand_id = hand_id_list[i]  # 手的ID
                hand_palm_center = hand[2]  # 手的掌心坐标
                hand_size = self.get_hand_size(hand)  # 手的大小

                self.debugPrint('condition charge')
                # 条件判断
                condition = False
                if self.x_range[0] <= hand_palm_center[0] <= self.x_range[1]:
                    if self.y_range[0] <= hand_palm_center[1] <= self.y_range[1]:
                        if hand_size >= self.size_threshold and gesture_list[i] == self.recharge_gesture:
                            if self.need_click_state is None:
                                condition = True  # 满足条件
                            elif click_state_list[i] == self.need_click_state:
                                condition = True  # 满足条件

                if condition:
                    self.debugPrint('满足条件')
                    # 满足条件
                    # 是否处于充能
                    if not self.recharge_signal:  # * 未处于充能状态
                        # 更新ID
                        self.recharge_hand_id = hand_id
                        self.recharge_hand_id_alive = True
                        # 发出充能信号
                        self.recharge_signal = True
                        # 重置开始充能的时间
                        self.recharge_time = time.time()

                    else:  # * 正处于充能状态
                        # 比较ID是否是当前充能的ID
                        if hand_id == self.recharge_hand_id:  # 是充能ID，则ID肯定存活
                            # ID充能判断
                            if self.recharge_power >= self.recharge_power_threshold:  # ! 充能完成
                                # ! 更新完成标志，更新完成时间
                                self.recharge_complete = True
                                self.recharge_complete_time = time.time()
                                self.debugPrint('enter next state!')  # ? 打印输出
                                # ! 返回结果，充能已完成
                                return 'recharge complete'
                            elif 0 <= self.recharge_power < self.recharge_power_threshold:  # 充能未完成
                                self.recharge_power += self.recharge_increment_per_frame  # 充能
                                self.recharge_id_info = {'size': hand_size,
                                                         'center': hand_palm_center}  # 更新ID充能时的信息
                                self.debugPrint(self.recharge_power)  # ? 打印输出
                        else:  # ID不是当前充能的ID
                            self.debugPrint('ID不是当前充能的ID')
                            # 充能ID是否存活
                            if not self.recharge_hand_id_alive:  # 充能ID已消失
                                # 满足条件，且原充能ID已消失
                                # 将比较大小和位置，若偏差在范围内，将更新ID
                                # 计算大小和位置偏差
                                size_deviation = np.abs(hand_size - self.ID_disappear_info['size'])
                                position_deviation = np.sqrt(
                                    (hand_palm_center[0] - self.ID_disappear_info['center'][0]) ** 2 + \
                                    (hand_palm_center[1] - self.ID_disappear_info['center'][1]) ** 2)
                                # ! 大小偏差范围判断 ，位置范围偏差判断
                                if size_deviation <= self.disappear_size_deviation and position_deviation <= self.disappear_position_deviation:
                                    # 偏差在范围内，将更新ID状态
                                    self.recharge_hand_id = hand_id  # 更新ID号
                                    self.recharge_hand_id_alive = True  # 更新存活标志
                                    self.ID_disappear_info = {}  # 重置消失时刻ID（前ID）的信息
                                    self.debugPrint('ID被更新！！！')
                else:
                    self.debugPrint('不满足条件')
                    # 不满足条件
                    # 是否处于充能状态
                    if self.recharge_signal:  # * 处于充能状态
                        # 比较ID是否是当前充能的ID
                        if hand_id == self.recharge_hand_id:  # 是充能ID，则ID肯定存活
                            # 不满足条件，将减少充能数
                            self.recharge_power -= self.recharge_decrease_per_frame
                            self.debugPrint(self.recharge_power)  # ? 打印输出
                            if self.recharge_power < 0:  # ! 小于初始值，重置当前状态
                                self.__init__(isReset=True)
                                return 'reset state'
                # 更新充能率
                self.update_recharge_rate()

    # five和fist手势判断
    def five_fist_recharge(self, handPose_list, gesture_list):
        if not self.fist_recharge.recharge_signal:  # 如果fist没在充能
            if self.five_recharge.recharge(handPose_list, gesture_list) == 'recharge complete':
                print('充能已完成')
                # 重置状态
                self.five_recharge.__init__(isReset=True)
                return 'five Out'
            self.update_rate('next_rate', self.five_recharge)
            print('five power rate: ', self.five_recharge.recharge_rate, self.five_recharge.recharge_id_info['size'])  # 显示充能完成率
        if not self.five_recharge.recharge_signal:  # 如果five没在充能
            if self.fist_recharge.recharge(handPose_list, gesture_list) == 'recharge complete':
                print('充能已完成')
                # 重置状态
                self.fist_recharge.__init__(isReset=True)
                return 'fist Out'
            self.update_rate('back_rate', self.fist_recharge)
            print('fist power rate: ', self.fist_recharge.recharge_rate, self.fist_recharge.recharge_id_info['size'])  # 显示充能完成率


    def windowLocation(self):
        value = self.state.split(' ')[0]
        info = {'isChange': True, 'name': 'location', 'value': value}
        self.q.put(info)

    def update_rate(self, name, recharge):
        info = {'isChange': True, 'name': 'pro_rate', 'value': (f'{name}', recharge.recharge_rate)}
        if self.state == 'control page':
            info['name'] = 'pro_rate_controlPage'
        self.q.put(info)

    def update_state(self, handPose_list, gesture_list, hands_angle_list):
        state = self.state
        if self.state == 'index page':
            print(self.state)
            five_fist_result = self.five_fist_recharge(handPose_list, gesture_list)
            if five_fist_result == 'five Out':
                self.state = 'schedule page'
            elif five_fist_result == 'fist Out':
                self.state = 'healthy page'

        elif self.state == 'schedule page':
            print(self.state)
            five_fist_result = self.five_fist_recharge(handPose_list, gesture_list)
            if five_fist_result == 'five Out':
                self.state = 'control page'
            elif five_fist_result == 'fist Out':
                self.state = 'index page'

        elif self.state == 'control page':
            print(self.state)
            five_fist_result = self.five_fist_recharge(handPose_list, gesture_list)
            if five_fist_result == 'five Out':
                self.state = 'healthy page'
            elif five_fist_result == 'fist Out':
                self.state = 'schedule page'

        elif self.state == 'healthy page':
            print(self.state)
            five_fist_result = self.five_fist_recharge(handPose_list, gesture_list)
            if five_fist_result == 'five Out':
                self.state = 'index page'
            elif five_fist_result == 'fist Out':
                self.state = 'control page'

        if self.state != state:
            self.windowLocation()
