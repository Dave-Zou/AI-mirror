# 加载QT界面和多线程
import time
from typing import List
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

        # 状态
        self.state = self.State()

        # 初始化five条件充能
        self.five_recharge = self.condition_charge(recharge_gesture=('five',))
        self.five_recharge.size_threshold = 50
        self.five_recharge.recharge_name = 'next'

        # 初始化fist条件充能
        self.fist_recharge = self.condition_charge(recharge_gesture=('fist',))
        # 修改充能条件
        self.fist_recharge.need_click_state = None # 不需要判断Click
        self.fist_recharge.x_range = (140, 500)  # 缩小X范围
        self.fist_recharge.y_range = (90, 400) # 缩小Y范围
        self.fist_recharge.size_threshold = 20 # 减小充能大小阈值
        self.fist_recharge.disappear_position_deviation = 40 # 增大消失重置位置偏差
        self.fist_recharge.recharge_name = 'back'

        # 手指指向条件充能
        self.choose_recharge = self.condition_charge(recharge_gesture=('one', 'gun'))
        # 修改充能条件
        self.choose_recharge.need_click_state = None # 不需要判断Click
        self.choose_recharge.x_range = (140, 500)  # 缩小X范围
        self.choose_recharge.y_range = (90, 400) # 缩小Y范围
        self.choose_recharge.size_threshold = 30 # 充能大小范围
        self.choose_recharge.ID_disappear_time_threshold = 1 # 消失重置时间范围
        self.choose_recharge.recharge_name = 'choose'

        # 倒退充能
        self.back_recharge = self.quit_recharge()


    class State:
        def __init__(self, order=0):
            # 状态列表
            self.state_list = ['index page', 'schedule page', 'control page', 'healthy page']
            # 序号
            self.state_order = order
            # 状态
            self.state = self.state_list[self.state_order]
            # 子状态
            self.subStates_level = [0 for _ in self.state_list]
            # 长度
            self.length = len(self.state_list)

        def enterSubState(self):
            self.subStates_level[self.state_order] += 1

        def exitSubState(self):
            self.subStates_level[self.state_order] -= 1

        # 子状态属性
        @property
        def subState(self):
            return self.subStates_level[self.state_order]
        # 子状态属性设置
        @subState.setter
        def subState(self, value):
            self.subStates_level[self.state_order] = value

        def nextState(self):
            self.state_order += 1
            if self.state_order >= self.length:
                self.state_order = 0
            self.state = self.state_list[self.state_order]

        def previousState(self):
            self.state_order -= 1
            if self.state_order < 0:
                self.state_order = self.length - 1
            self.state = self.state_list[self.state_order]

        def __add__(self, other):
            print('add ', other)
            if other > 0:
                for i in range(other):
                    self.nextState()
            if other < 0:
                for i in range(-other):
                    self.previousState()
            return self

        def __iadd__(self, other):
            self.__add__(other)

        def __sub__(self, other):
            if other < 0:
                for i in range(other):
                    self.nextState()
            if other > 0:
                for i in range(-other):
                    self.previousState()
            return self

        def __isub__(self, other):
            self.__sub__(other)


        def __str__(self):
            return self.state

        def __eq__(self, other):
            return self.state == other


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

    # 数据传入，处理中心
    def main(self, handPose_list, gesture_list, hands_angle_list):
        self.update_state(handPose_list, gesture_list, hands_angle_list)

    # 手势条件充能类
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
            # recharge_complete_info: 充能完成时的信息，原始hand关键点信息 和 hand_size

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
                self.recharge_complete_info = {'hand': None, 'hand_size': None}
                self.recharge_name = None

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

        def reset(self):
            self.recharge_hand_id = -1
            self.recharge_hand_id_alive = False
            self.ID_disappear_time = None
            self.ID_disappear_info = {}

            self.recharge_signal = False
            self.recharge_power = 0

            self.recharge_id_info = {'size': 0, 'center': (0, 0)}

            self.recharge_rate = 0

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
                # ID： 如果在判定中ID消失，记录下消失时刻之前的大小和位置，如果在范围内产生满足条件的新ID，
                #      且大小和位置与前ID偏差较小，则更新ID。期间充能暂停。否则，重置状态。

                hand_id = hand_id_list[i]  # 手的ID
                hand_palm_center = hand[2]  # 手的掌心坐标
                hand_size = self.get_hand_size(hand)  # 手的大小

                self.debugPrint('condition charge')
                # 条件判断
                condition = False
                if self.x_range[0] <= hand_palm_center[0] <= self.x_range[1]:
                    if self.y_range[0] <= hand_palm_center[1] <= self.y_range[1]:
                        if hand_size >= self.size_threshold and gesture_list[i] in self.recharge_gesture:
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
                                # ! 更新完成标志，更新完成时间，记录完成时刻信息
                                self.recharge_complete = True
                                self.recharge_complete_time = time.time()
                                self.recharge_complete_info['hand'] = hand
                                self.recharge_complete_info['size'] = hand_size
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

    # 倒退充能类
    class quit_recharge:
        def __init__(self, isReset=None):
            # start_recharge: 开始充能
            # recharge_signal: 是否充能信号
            # recharge_time_threshold: 充能完成的时间阈值
            # pause_time_threshold: 暂停重置的时间阈值
            # recharge_rate: 充能完成率（0-100）
            # current_time: 充能时更新存储的当前时间，用于充能判断
            # recharge_name: 充能名称

            if not isReset: # 非手动重置的部分，即常量
                self.recharge_time_threshold = 8
                self.pause_time_threshold = 1.5

            self.recharge_rate = 0
            self.current_time = 0
            self.start_recharge = False
            self.recharge_signal = False
            self.recharge_name = 'quit'


        def reset(self): # 重置所有变量
            self.__init__(isReset=True)

        def startRecharge(self): # 开始充能计时
            self.start_recharge = True
            self.recharge_signal = True
            self.start_recharge_time = time.time()

        def pauseRecharge(self): # 暂停
            if self.recharge_signal: # 暂停未暂停的充能
                self.recharge_signal = False
                self.pause_recharge_time = time.time()
            else: # 暂停已暂停的充能，将进入暂停重置计时
                if time.time() - self.pause_recharge_time > self.pause_time_threshold:
                    self.reset()

        def continueRecharge(self):
            if self.start_recharge: # 开启充能状态
                self.recharge_signal = True
                self.start_recharge_time += time.time() - self.pause_recharge_time

        def update_recharge_rate(self):
            if self.start_recharge and self.recharge_signal:
                rate = (self.current_time - self.start_recharge_time) / self.recharge_time_threshold * 100
                self.recharge_rate = rate

        def recharge(self, QuitCondition=None):
            if QuitCondition is None:
                return

            if QuitCondition: #? 满足倒退充能的条件
                if not self.start_recharge:  #? 没有开始充能
                    self.startRecharge()  # 开启充能开关
                else:  #? 已经开始充能
                    if self.recharge_signal:  # 处于暂停状态
                        self.continueRecharge()  # 将暂停状态取消
            else: #? 不满足倒退充能的条件
                if self.back_recharge.start_recharge:  #? 已经开始充能
                    self.back_recharge.pauseRecharge()  # 暂停充能
                else:  #? 没有开始充能
                    pass

            if not self.start_recharge:
                return 'not start'

            if not self.recharge_signal: # 暂停中
                return 'pausing...'

            self.current_time = time.time()
            self.update_recharge_rate()

            if self.current_time - self.start_recharge_time > self.recharge_time_threshold:
                return 'complete recharge'



    # 对手势进行条件充能
    def more_gesture_recharge(self, recharges, handPose_list, gesture_list, has_back_recharge=False):
        result = None # 返回结果
        has_been_recharge = False

        for gesture_recharge in recharges:
            if gesture_recharge.recharge_signal: # 是否条件充能中已有开始充能
                has_been_recharge = True
                # 如果此充能已开始，则继续
                if gesture_recharge.recharge(handPose_list, gesture_list) == 'recharge complete':
                    print(f'{gesture_recharge.recharge_name}充能已完成')
                    gesture_recharge.reset()
                    gesture_recharge.recharge_rate = 100
                    result = f'{gesture_recharge.recharge_name} Out'

                self.update_rate(gesture_recharge)
                print('recharge state: ', gesture_recharge.recharge_name, gesture_recharge.recharge_rate)

        # 都没有开始充能，则尝试对每个条件充能
        if not has_been_recharge:
            for gesture_recharge in recharges:
                gesture_recharge.recharge(handPose_list, gesture_list)
                # 如果在条件充能后，开始充能了，则不再继续判断后续的条件充能
                if gesture_recharge.recharge_signal:
                    has_been_recharge = True
                    break

        if has_back_recharge:
            if not has_been_recharge: # 满足倒退充能的条件（没有手势在充能）
                back_recharge = self.back_recharge.recharge(QuitCondition=True)
            else: # 不满足倒退充能的条件（存在手势充能）
                back_recharge = self.back_recharge.recharge(QuitCondition=False)
            if back_recharge == 'complete recharge':
                result = 'quit Out'
            self.update_rate(self.back_recharge)

        return result

    # 跳转页面
    def windowLocation(self):
        value = self.state.state.split(' ')[0]
        info = {'isChange': True, 'name': 'location', 'value': value}
        self.q.put(info)

    # 更新显示进度
    def update_rate(self, recharge):
        # 默认为前进后退进度
        rate_name = 'next_back_rate'
        if recharge.recharge_name == 'choose': # 充能名为choose
            if self.state == 'schedule page': # 当前页面
                rate_name = 'choose_rate_for_schedule' # 设置进度名称
            elif self.state == 'control page': # 当前页面
                rate_name = 'choose_rate_for_control' # 设置进度名称

        elif recharge.recharge_name == 'quit':
            rate_name = 'quit_rate'

        info = {'isChange': True, 'name': rate_name, 'value': (f'{recharge.recharge_name}', recharge.recharge_rate)}
        self.q.put(info)

    # -----------------------------------------------------------------------------------------------------------------
    # 充能处理
    def recharge_pro(self, handPose_list, gesture_list, gesture_recharge_add=None):
        gestures = [self.five_recharge, self.fist_recharge]
        if gesture_recharge_add is not None:
            gestures += gesture_recharge_add

        recharge_result = self.more_gesture_recharge(gestures, handPose_list, gesture_list)

        print(recharge_result) #? 打印输出
        if recharge_result == 'next Out' and self.state.subState == 0:
            self.state.nextState()
        elif recharge_result == 'back Out' and self.state.subState == 0:
            self.state.previousState()

        elif recharge_result == 'choose Out':
            self.state.subState += 1

        elif recharge_result == 'quit Out':
            self.state.subState -= 1

    # -----------------------------------------------------------------------------------------------------------------

    # 根据传入数据，更新状态
    def update_state(self, handPose_list, gesture_list, hands_angle_list):
        state = self.state.state
        print(state) #? 打印输出

        if self.state == 'index page':
            print(self.state)
            self.recharge_pro(handPose_list, gesture_list)


        elif self.state == 'schedule page':
            print(self.state)
            self.recharge_pro(handPose_list, gesture_list)

        elif self.state == 'control page':
            print(self.state)
            if self.state.subState == 0:
                self.recharge_pro(handPose_list, gesture_list, gesture_recharge_add=[self.choose_recharge])
            elif self.state.subState == 1:
                print('control sub-state')

        elif self.state == 'healthy page':
            print(self.state)
            if self.state.subState == 0:
                self.recharge_pro(handPose_list, gesture_list,  gesture_recharge_add=[self.choose_recharge])

        if self.state != state:
            self.windowLocation()

