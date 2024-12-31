import copy
import random
import matplotlib.pyplot as plt
from Instance import Job,State,Machine,PT,agv_num
import numpy as np

class AGV:
    def __init__(self,idx,L_U):
        self.idx=idx
        self.cur_site=L_U
        self.using_time=[]
        self._on=[]
        self._to=[]
        self.end=0
        self.job_wait_time=[]

    def ST(self,s,t1,t2):
        start=max(s,self.end+t1)
        return start-t1,start+t2

    def update(self,s,trans1,trans2,J_site,J_m,_on=None,job_end=0):
        self.job_wait_time.append([_on,job_end,self.end])
        self.using_time.append([s,s+trans1])
        self.using_time.append([s + trans1, s+trans1 + trans2])
        self._on.append(None)
        self._on.append(_on)
        self._to.extend([J_site,J_m])
        self.end=s+trans1+trans2
        self.cur_site=J_m
        return _on,J_m,s+trans1 + trans2

class Item:
    def __init__(self,idx):
        self.idx=idx
        self.start=[]
        self.end=[]
        self.op_list=[]
        self._on=[]
        self.T=[]
        self.last_ot=0
        self.L=0
        self.laston=None
        self.op=0  #对于机器来说是加工物品的个数，对于工件来说是当前工序
        self.job_wait_time=[]
        self.meachine_wait_time=[]

    def update(self,s,e,on,t,op,A_T):
        if len(self.end)==0:
            self.meachine_wait_time.append([on,A_T,A_T])
        else:
            if A_T>self.end[-1]:
                self.meachine_wait_time.append([on,A_T,self.end[-1]])
        self.start.append(s)
        self.end.append(e)
        self.job_wait_time.append([on,s,A_T])
        self.op_list.append(op)
        self._on.append(on)
        self.laston=on
        self.T.append(t)
        self.last_ot=e
        self.L+=t
        self.op+=1


class Scheduling:
    def __init__(self,J_num,Machine,State,PT,TT,agv_num):
        self.M=Machine
        self.J_num=J_num
        self.agv_num=agv_num
        self.TT=TT
        self.State=State
        self.PT=PT
        self.Create_Job()
        self.Create_Machine()
        self.Create_Agv(Machine)
        self.fitness=0

    def Create_Job(self):
        self.Jobs=[]
       # M=Item(0)
        for i in range(self.J_num):
            J=Item(i+1)
            J.laston=0
            self.Jobs.append(J)

    def Create_Machine(self):
        self.Machines=[]
        idx=1
        for i in range(len(self.M)):    #突出机器的阶段性，即各阶段有哪些机器
            State_i=[]
            for j in range(self.M[i]):
                M=Item(idx)
                State_i.append(M)
                idx+=1
            self.Machines.append(State_i)
    def Create_Agv(self,m):
        self.Agvs=[]
        for i in range(self.agv_num):
            A=AGV(i,sum(m)+1)
            self.Agvs.append(A)
    #每个阶段的解码
    def Stage_Decode(self,CHS,Stage):

        for i in CHS:
            last_od=self.Jobs[i].last_ot
            last_Md=[self.Machines[Stage][M_i].last_ot for M_i in range(self.M[Stage])] #机器的完成时间
            last_ML = [self.Machines[Stage][M_i].L for M_i in range(self.M[Stage])]     #机器的负载
            M_time=[self.PT[Stage][M_i][i] for M_i in range(self.M[Stage])]             #机器对当前工序的加工时间
            O_et=[last_Md[_]+M_time[_] for _ in range(self.M[Stage])]
            if O_et.count(min(O_et))>1 and last_ML.count(last_ML)>1:
                Machine=random.randint(0,self.M[Stage])
            elif O_et.count(min(O_et))>1 and last_ML.count(last_ML)<1:
                Machine=last_ML.index(min(last_ML))
            else:
                Machine=O_et.index(min(O_et))
            best_s,best_e,t1,t2=None,None,None,None
            min_tf=99999
            best_agv=None
            Machineidx=sum(self.M[0:Stage])+Machine+1
            # print(Machineidx)
            # print("***********")
            # print(Stage)
            for agv in self.Agvs:
                trans1=self.TT[agv.cur_site][self.Jobs[i].laston]
                trans2=self.TT[self.Jobs[i].laston][Machineidx]
                start,end=agv.ST(self.Jobs[i].last_ot,trans1,trans2)
                if end<min_tf:
                    best_s,best_e,t1,t2 = start,end,trans1,trans2
                    best_agv=agv
                    min_tf=best_e
            J,D,T=best_agv.update(best_s,t1,t2,self.Jobs[i].laston,Machineidx,self.Jobs[i].idx,self.Jobs[i].last_ot)
            # 无AGV
            #s, e, t=max(last_od,last_Md[Machine],),max(last_od,last_Md[Machine])+M_time[Machine],M_time[Machine]

            #有AGV
            s, e, t=max(last_Md[Machine],max(last_od,best_e)),max(last_Md[Machine],max(last_od,best_e))+M_time[Machine],M_time[Machine]
            self.Jobs[i].update(s, e,Machineidx, t,0,T)
            self.Machines[Stage][Machine].update(s, e,i, t,self.Jobs[i].op,T)
            if e>self.fitness:
                self.fitness=e

    #解码
    def Decode(self,CHS):
        for i in range(self.State):
            self.Stage_Decode(CHS,i)
            Job_end=[self.Jobs[i].last_ot for i in range(self.J_num)]
            CHS = sorted(range(len(Job_end)), key=lambda k: Job_end[k], reverse=False)

    #画甘特图
    def Gantt(self):
        #fig = plt.figure()
        fig=plt.figure(figsize=(15, 8))  # 设置DPI为100
        M = ['red', 'blue', 'yellow', 'orange', 'green', 'moccasin', 'purple', 'pink', 'navajowhite', 'Thistle',
             'Magenta', 'SlateBlue', 'RoyalBlue', 'Aqua', 'floralwhite', 'ghostwhite', 'goldenrod', 'mediumslateblue',
             'navajowhite','navy', 'sandybrown']
        M_num=0
        for i in range(len(self.M)):
            op_time=0
            for j in range(self.M[i]):
                work_time=0
                for k in range(len(self.Machines[i][j].start)):
                    Start_time=self.Machines[i][j].start[k]
                    End_time=self.Machines[i][j].end[k]
                    Job=self.Machines[i][j]._on[k]
                    op=self.Machines[i][j].op_list[k]
                    plt.barh(M_num, width=End_time - Start_time, height=0.8, left=Start_time, \
                             color=M[Job%20], edgecolor='black')
                    plt.text(x=Start_time+1, y=M_num-0.10 ,
                             s="J"+str(Job+1)+"|T"+str(op), size=12, fontproperties='Times New Roman')
                    op_time+=(End_time-Start_time)
                    work_time+=(End_time-Start_time)
                M_num += 1
                print(f"meachine{M_num} work rate: {work_time/self.fitness}")
            print(f"op{i+1} work rate: {op_time/self.fitness}")


        opline=[sum(Machine[0:i+1])-0.5 for i in range(len(Machine))]

        # for i in range(len(opline)):
        #     plt.hlines(opline[i],xmin=0,xmax=500, colors='black',linestyles='solid',label="OP"+str(i+1))
        plt.yticks(np.arange(M_num + 1), np.arange(1, M_num + 2), size=20, fontproperties='Times New Roman')
        plt.xticks(size=20, fontproperties='Times New Roman')
        plt.ylabel("机器", size=20, fontproperties='SimSun')
        plt.xlabel("时间", size=20, fontproperties='SimSun')
        plt.tick_params(labelsize=20)
        plt.tick_params(direction='in')
        plt.show()

    def api_return(self):
        machinelists=[]
        agvlist=[]
        for i in range(len(self.M)):
            for j in range(self.M[i]):
                machinelist=[]
                for k in range(len(self.Machines[i][j].start)):
                    item_list=[]
                    Start_time=self.Machines[i][j].start[k]
                    End_time=self.Machines[i][j].end[k]
                    op=self.Machines[i][j].op_list[k]
                    Job=self.Machines[i][j]._on[k]
                    #item_list.append(self.Machines[i][j].idx)
                    item_list.append(Job+1)
                    item_list.append(Start_time)
                    item_list.append(End_time)
                    item_list.append(op)
                    machinelist.append(item_list)
                machinelists.append(machinelist)

        agv_num=0

        agvlists=[]
        for agv in self.Agvs:
            agv_loc=sum(self.M)+1
            agvlist=[]
            to_num=0
            for use_time in agv.using_time:
                item_list=[]
                Start_time=use_time[0]
                End_time=use_time[1]
                to=agv._to[to_num]
                if to==agv_loc:
                    continue
                on=agv._on[to_num]
                to_num+=1
                #item_list.append(agv.idx)
                if on==None:
                    item_list.append(0)
                else:
                    item_list.append(on)
                item_list.append(Start_time)
                item_list.append(End_time)
                item_list.append(agv_loc)
                item_list.append(to)
                agvlist.append(item_list)
                agv_loc=to
            agvlists.append(agvlist)
            agv_num+=1
        wait_times,meachines_block_time,wait_rate,block_rate,agvs_block_time,agv_block_rates=self.get_block_and_wait()
        self.Gantt_html(machinelists,agvlists,wait_rate,block_rate,agv_block_rates)
        print(wait_times,meachines_block_time,wait_rate,block_rate,agvs_block_time,agv_block_rates)
        return machinelists,agvlists,block_rate,agv_block_rates

    def Gantt_html(self,machinelists,agvlists,wait_rate,block_rate,agv_block_rates):
        import re
        # 读取原始HTML文件
        with open('gantt.html', 'r', encoding='utf-8') as file:
            content = file.read()
        # 新的ganttData值，这里只是一个示例，你需要替换成你想要设置的值
       # new_gantt_data = str(meachines_tasks)[0:-1]
        # 使用正则表达式替换var ganttData的值
        # 这个正则表达式匹配 var ganttData = 开头，直到后面的 JavaScript 代码块结束
        # 它假设 ganttData 的值是多行的，并且可能包含引号和换行符
        new_content = re.sub(r'(var meachine_ganttData =\s*).*?(\];)', r'\1' + str(machinelists)[0:-1] + r'\2', content, flags=re.DOTALL)
        new_content = re.sub(r'(var agv_ganttData =\s*).*?(\];)', r'\1' + str(agvlists)[0:-1] + r'\2', new_content, flags=re.DOTALL)
        new_content = re.sub(r'(var wait_rate =\s*).*?(\];)', r'\1' + str(wait_rate)[0:-1] + r'\2', new_content, flags=re.DOTALL)
        new_content = re.sub(r'(var block_rate =\s*).*?(\];)', r'\1' + str(block_rate)[0:-1] + r'\2', new_content, flags=re.DOTALL)
        new_content = re.sub(r'(var agv_block_rate =\s*).*?(\];)', r'\1' + str(agv_block_rates)[0:-1] + r'\2', new_content, flags=re.DOTALL)
        # 将修改后的内容写回原HTML文件
        with open('gantt.html', 'w', encoding='utf-8') as file:
            file.write(new_content)

    def merge_intervals(self,intervals):
        # 首先，按照区间的起始点对区间进行排序
        intervals.sort(key=lambda x: x[0])
        # 初始化合并后的区间列表
        merged = []
        # 遍历排序后的区间列表
        for interval in intervals:
            # 如果合并后的区间列表为空，或者当前区间与合并后的最后一个区间不重叠
            if not merged or merged[-1][1] < interval[0]:
                # 将当前区间添加到合并后的区间列表中
                merged.append(interval)
            else:
                # 否则，合并当前区间与合并后的最后一个区间
                merged[-1][1] = max(merged[-1][1], interval[1])
        return merged


    def get_block_and_wait(self):
        wait_times=[]
        wait_time=0
        for i in range(len(self.M)):
            for j in range(self.M[i]):
                wait_time=0
                for T in self.Machines[i][j].meachine_wait_time:
                    wait_time+=T[1]-T[2]
                wait_times.append(wait_time)


        block_times=[[] for _ in range(sum(Machine))]
        for job in self.Jobs:
            for bt in job.job_wait_time:
                block_time=[]
                block_time.append(bt[2])
                block_time.append(bt[1])
                block_times[int(bt[0])-1].append(block_time)

        meachines_block_time=[]
        for bl in block_times:
            if len(bl)!=0:
                meachine_block_time=0
                bl_merge=self.merge_intervals(bl)
                for x in bl_merge:
                    meachine_block_time+=(x[1]-x[0])
                meachines_block_time.append(meachine_block_time)
            else:
                meachines_block_time.append(0)

        agv_block_times=[[] for _ in range(agv_num)]
        index=0
        for agv in self.Agvs:
            for bt in agv.job_wait_time:
                agv_block_time=[]
                if bt[1]<bt[2]:
                    agv_block_time.append(bt[1])
                    agv_block_time.append(bt[2])
                    agv_block_times[index].append(agv_block_time)
            index+=1

        agvs_block_time=[]
        for bl in agv_block_times:
            if len(bl)!=0:
                agv_block_time=0
                bl_merge=self.merge_intervals(bl)
                for x in bl_merge:
                    agv_block_time+=(x[1]-x[0])
                agvs_block_time.append(agv_block_time)
            else:
                agvs_block_time.append(0)

        wait_rates=[]
        block_rates=[]

        index=0
        for i in range(len(self.M)):
            for j in range(self.M[i]):
                end=self.Machines[i][j].end[-1]
                start=self.Machines[i][j].start[0]
                wait_rates.append(wait_times[index]/(end-start))
                block_rates.append(meachines_block_time[index]/(end-start))
                index+=1

        agv_block_rates=[]
        index=0
        for agv in self.Agvs:
            start=agv.using_time[0][0]
            end=agv.using_time[-1][-1]
            agv_block_rates.append(agvs_block_time[index]/(end-start))
            index+=1


        return wait_times,meachines_block_time,wait_rates,block_rates,agvs_block_time,agv_block_rates




    def Agv_Gantt(self):
        #fig = plt.figure()
        fig=plt.figure(figsize=(24, 10))  # 设置DPI为100
        M = ['red', 'blue', 'yellow', 'orange', 'green', 'moccasin', 'purple', 'pink', 'navajowhite', 'Thistle',
             'Magenta', 'SlateBlue', 'RoyalBlue', 'Aqua', 'floralwhite', 'ghostwhite', 'goldenrod', 'mediumslateblue',
             'navajowhite','navy', 'sandybrown']
        agv_num=0

        for agv in self.Agvs:
            to_num=0
            _or=sum(self.M)+1
            for use_time in agv.using_time:
                Start_time=use_time[0]
                End_time=use_time[1]
                to=agv._to[to_num]
                on=agv._on[to_num]
                if on==None:
                    on=0
                if (Start_time-End_time)!=0:
                    plt.barh(agv_num, width=End_time - Start_time, height=0.8, left=Start_time, \
                             color=M[on%len(M)], edgecolor='black')
                    plt.text(x=Start_time +1, y=agv_num-0.08 ,
                             s="J"+str(on)+"|O"+str(_or)+"|D"+str(to), size=11, fontproperties='Times New Roman')
                to_num+=1
                _or=to
            agv_num+=1
        #opline=[sum(Machine[0:i+1])-0.5 for i in range(len(Machine))]

        # for i in range(len(opline)):
        #     plt.hlines(opline[i],xmin=0,xmax=500, colors='black',linestyles='solid',label="OP"+str(i+1))
        plt.yticks(np.arange(agv_num + 1), np.arange(1, agv_num + 2), size=20, fontproperties='Times New Roman')
        plt.xticks(size=20, fontproperties='Times New Roman')
        plt.ylabel("AGV", size=20, fontproperties='SimSun')
        plt.xlabel("Time", size=20, fontproperties='SimSun')
        plt.tick_params(labelsize=20)
        plt.tick_params(direction='in')
        plt.show()



#
