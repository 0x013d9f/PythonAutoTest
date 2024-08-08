import threading
import time
import subprocess
from datetime import datetime, timedelta


class LogAnalyze(threading.Thread):
    """
    log_type_dict: 用于记录日志统计信息
    """
    log_type_dict = {
        'V': {
            'name': '详细',
            'total': 0,
        },
        'D': {
            'name': '调试',
            'total': 0,
        },
        'I': {
            'name': '信息',
            'total': 0,
        },
        'W': {
            'name': '警告',
            'total': 0,
        },
        'E': {
            'name': '错误',
            'total': 0,
        },
        'F': {
            'name': '致命',
            'total': 0,
        },
    }

    def __init__(self, threadID, name, log_save_path, *print_level):
        """
        初始化日志分析记录器
        :param threadID: 线程ID
        :param name: 线程名
        :param log_save_path: 日志保存路径 执行期间的日志保存路径+文件名
        :param print_level: 需要输出的日志等级(V、D、I、W、E、F)
        """
        super().__init__()
        self.threadID = threadID
        self.name = name
        self.print_level = print_level
        self.exit_flag = False
        self.log_save_path = log_save_path

    def run(self):
        print("Starting " + self.name)
        self.exit_flag = False
        self.get_and_save_log()
        print("Exiting " + self.name)

    def exit(self):
        # 结束日志记录
        self.exit_flag = True
        return self.exit_flag

    def save_log(self, data):
        # 把日志记录保存到txt文件
        w_data = ['--------- beginning of main\n']
        w_data.extend(_ + '\n' for _ in data['main'])
        w_data.extend('--------- beginning of system\n')
        w_data.extend(_ + '\n' for _ in data['system'])
        with open(self.log_save_path, 'w', encoding='utf-8') as file:
            file.writelines(w_data)

    def get_and_save_log(self):
        last_time = datetime.now() - timedelta(seconds=2)
        log_data = {
            'main': [],
            'system': []
        }
        while not self.exit_flag:
            """
            * last_time *
                数据 last_time 是 datetime 类型的时间，内有时间各部分作为自身属性可以直接读取
                其数据类型为 int 类型
            
            # adb shell logcat -t 24 - 08 - 08 17:02:34.241
            time_format = last_time.strftime('%y - %m - %d %H:%M:%S.%f')[:-3]
            该版本时间字符串会在当前时间的分钟在0~9之时，无法获取到日志，执行命令会提示错误如下错误：
                logcat: Invalid filter expression '17:02:34.241'.
            
            # adb shell logcat -t 2024 - 8 - 8 17:12:17.176
            time_format = (f"{last_time.year} - {last_time.month} - {last_time.day} "
                           f"{last_time.hour}:{last_time.minute}:{last_time.second}.{str(last_time.microsecond)[:-3]}")
            修改：手动将时间模板化，时间各部分不会存在前导0作为占位填充
            该版本时间字符串会使得根据时间截取log操作失效，导致大量不属于期待时间范围的日志被输出
            推测原因是由于时间字符串中的“年份”为“2024”引起的，将年份截取后即为最终版本，暂未发现bug
            """
            # 获取上次获取的日志时间并构造日志获取cmd命令
            # adb shell logcat -t 24 - 8 - 8 17:12:17.176
            time_format = (f"{str(last_time.year)[2:]} - {last_time.month} - {last_time.day} "
                           f"{last_time.hour}:{last_time.minute}:{last_time.second}.{str(last_time.microsecond)[:-3]}")
            cmd = f'adb shell logcat -t {time_format}'

            # 获取日志并记录获取时间
            """
            使用 subprocess 的 Popen 去执行 cmd 命令并获取到执行命令后输出在命令行窗口的数据
            将数据在Python进行处理
            
            同时使用其是为了解决使用 os.popen获取命令行输出内容为英文时，调用 read() 方法获取输出数据的字符串格式
            在内容存在中文时会出现解码错误，read()使用的解码方式为GBK，使用subprocess设置解码方式为 utf-8
            """
            now = datetime.now()
            result = subprocess.Popen(
                cmd,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8'
            )
            stdout, stderr = result.communicate()
            # print(stdout) # 调试用

            # 处理日志
            self.log_process(stdout, last_time, log_data, *self.print_level)

            # 更新上一次获取日志时间为执行命令的时间now
            last_time = now
            time.sleep(2)

            # 保存日志
            self.save_log(log_data)

    def log_process(self, log, ltime, save_data, *print_level):
        """
        对获取到的日志进行处理：
            1.清洗上次获取日志时间 ltime 之前的日志记录
                logcat会默认提供部分在目标时间之前的日志记录，提供上下文帮助排除错误
            2.格式化输出需要的日志
            3.保存新增的日志到 save_data 中

        :param log: logcat获取到的日志内容
        :param ltime: 上次获取日志的时间
        :param save_data: 用于保存获取到的新日志记录
            格式：main保存应用程序日志，system保存系统日志
                {'main': [],'system': []}
        :param print_level: 需要输出的日志等级，可变参数列表
        """
        # 初始化变量
        if print_level is None:
            print_level = tuple('E')
        system_log = []
        main_log = []
        log_list = None

        print('\n' * 5 + '-------------------')
        # 按行分割字日志记录，并去除空数据
        log_lines = log.split('\n')
        while '' in log_lines:
            log_lines.remove('')

        # 遍历日志记录
        for line in log_lines:
            if not line:
                break
            line = line.rstrip('\n')
            # 根据当前行判断内容，切换存储日志的列表
            if 'beginning of main' in line:
                log_list = main_log
                print(line)
            elif 'beginning of system' in line:
                log_list = system_log
                print(line)
            else:
                # 截取日志时间与日志类型
                log_block = line.split(' ')
                while '' in log_block:
                    log_block.remove('')
                log_time = datetime.strptime(log_block[0] + log_block[1], '%m-%d%H:%M:%S.%f')
                log_time = log_time.replace(year=2024)
                log_type = log_block[4]

                # 早于记录时间的日志跳过不进行记录
                if log_time < ltime:
                    continue

                # 统计日志类型，添加日志记录，输出指定类型的日志
                log_list.append(line)
                self.log_type_dict[log_type]['total'] += 1
                if log_type in print_level:
                    print(line)

        # 输出日志的统计信息
        for key in self.log_type_dict.keys():
            print(f'\t\t{self.log_type_dict[key]["name"]}: {self.log_type_dict[key]["total"]}')

        # 向日志记录中添加新日志
        save_data['main'].extend(main_log)
        save_data['system'].extend(system_log)
        print('-------------------')


if __name__ == '__main__':
    log_analyze_thread = LogAnalyze(1, "Thread-LogAnalyze", 'log.txt', 'W', 'E')
    log_analyze_thread.start()

    # TODO 进行一些业务操作，使用sleep暂时占位
    time.sleep(1)

    log_analyze_thread.exit()
