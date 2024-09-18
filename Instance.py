import random

import numpy as np
import pandas as pd

random.seed(32)

#State:阶段，即工件有几道工序，Job:工件数，Machine['type':list],对应各阶段的并行机数量
def Generate(State,Job,Machine):
    PT=[]
    for i in range(State):
        Si=[]       #第i各加工阶段
        for j in range(Machine[i]):
            S0=[random.randint(10,50) for k in range(Job)]
            Si.append(S0)
        PT.append(Si)
    agv1_trans = [random.randint(2,6) for i in range(1,sum(Machine)+1)]
    agv1_trans=trans_Matrix(agv1_trans,sum(Machine)+1)

    return PT,agv1_trans

def trans_Matrix(trans,m):
    T=np.zeros((m,m))
    for i in range(len(T)):
        for j in range(len(T[i])):
            if i==j:
                T[i][j]=0
            elif i!=j and T[i][j]==0:
                T[i][j]=sum(trans[i:j])
                T[j][i]=T[i][j]
    return T

def Fsp_Generate(State,Job,Machine):
    PT=[]
    df = pd.read_csv('E:\PYCHARM\pycharm project\Smart Factory\HFSP\加工时间-100s.csv')
    seed=df.values.tolist()
    for i in range(State):
        Si=[]       #第i各加工阶段
        for j in range(Machine[i]):
            S0=[int(seed[k][i]) for k in range(len(seed))]
            Si.append(S0)
        PT.append(Si)
    return PT


Job=100
State=4
Machine=[3,2,3,2]
agv_num=5
PT,agv_trans=Generate(State,Job,Machine)
#PT=Fsp_Generate(State,Job,Machine)
if __name__ == '__main__':
    # FSP_PT=Fsp_Generate(State,Job,Machine)
    print(agv_trans)