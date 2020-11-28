from gurobipy import GRB, Model, quicksum


#Conjuntos
H = range(0,2) #Horarios
Dias = range(0,28) #Días
M = range(1,5) #Tipos de Trabajador
N = range(1, 33) #Trabajador



restaurant = Model()

#Variables
T_nmhd = restaurant.addVars(N, M, H, Dias, vtype=GRB.BINARY, name='T') #Si el trabajador n de tipo m trabaja en el turno h del día d.
z_d = restaurant.addVars(Dias,vtype=GRB.BINARY, name='Abrir Local') #si el restaurante abre el día d.
k_d = restaurant.addVars(Dias,vtype=GRB.BINARY, name='Comprar Insumos') #  si se compran insumos el día d
I_d = restaurant.addVars(Dias,vtype=GRB.INTEGER, lb = 0, name='Cantidad Insumos Comprados') #Cantidad de insumos comprados el día d
B_d = restaurant.addVars(Dias,vtype=GRB.INTEGER, lb = 0, name='Cantidad de Insumos en Bodega') #Cantidad de insumos en el inventario en el día d


restaurant.update()



#Parámetros
D_hd = [[40, 50],[50, 60],[80, 90],[100, 120],[130, 220],[180, 250],[0,0],
        [40, 50],[50, 60],[80, 90],[100, 120],[130, 220],[180, 250],[0,0],
        [40, 50],[50, 60],[80, 90],[100, 120],[130, 220],[180, 250],[0,0],
        [40, 50],[50, 60],[80, 90],[100, 120],[130, 220],[180, 250],[0,0]] 
        # Demanda de clientes en el restaurante en el horario h el día d. **LISTA**
S = 24 #Espacio medido en metros cuadrados de la cocina
A = 300000 #Gasto de agua e higiene por persona.
CT_m = {1: 9000,
        2: 12000,
        3: 14000,
        4: 10000} #Costo de un Turno de un trabajador tipo m.
U = 8000 #Ganancia promedio entregada por persona.
L_f = 20000 #Gastos de luz diario promedio si el local est´a cerrado.
L_v = 40000 #Gastos de luz diario promedio si abre el local
B = 3075000 #Otros gastos mensuales fijos (internet, cable, etc.).
CM_m = 50 #Capacidad máxima de clientes por trabajador del tipo m.
I_p = 1 #Cantidad de insumos necesitados por persona.
C_i = 5000 #Costo promedio por insumo
v = 12000 #Volumen promedio de los insumos (cm^3)
V = 6000000 # Volumen de la bodega en cm^3.
C_k = 20000 #Costo de ir a comprar insumos.
X = 1000 # Ancho del espacio destinado a mesas.
Y =  1000#Largo del espacio destinado a mesas
r = 35 #cm #Radio de las mesas.
Q = 1000000000 #Número muy grande

#Restricciones

#R1.Personal suficiente atendiendo en el local

restaurant.addConstrs((quicksum(T_nmhd[n,m,h,d] for n in N)) * CM_m >= D_hd[d][h] for m in range(1,4) for h in H for d in Dias)
restaurant.addConstrs((quicksum(T_nmhd[n,4,h,d] for n in N)) == 1 for h in H for d in Dias if (d+1)%7!=0)

#R2.Cantidad máxima de personal en cocina (cada persona cuenta con al menos 4 metros cuadrados).

restaurant.addConstrs(S * 0.25 >= quicksum(T_nmhd[n,3,h,d] for n in N) for h in H for d in Dias) #Asumimos que cada trabajador ocupa 1m^2

#R3.Días domingo no se trabaja.

restaurant.addConstrs(z_d[d] == 0 for d in Dias if (d+1)%7==0  )

#R4.Deben haber suficientes insumos para los clientes.

restaurant.addConstrs(I_d[d] + B_d[d] >= quicksum(I_p * D_hd[d][h] for h in H) for d in Dias)

#R5.Cuando no hay suficientes insumos para satisfacer la demanda del dia se debe ir a comprar

restaurant.addConstrs(- (B_d[d] - quicksum(I_p * D_hd[d][h] for h in H)) <= k_d[d] * Q for d in Dias )
restaurant.addConstrs(- (B_d[d] - quicksum(I_p * D_hd[d][h] for h in H)) + Q  -1 >= k_d[d] * Q for d in Dias)

#R6.Lo que no se ocupa se guarda para el día siguiente.

restaurant.addConstrs(B_d[d] == B_d[d-1] - quicksum(I_p * D_hd[d][y]  for y in range(0,2))+ I_d[d-1] for d in Dias[1:28])

#R7.La bodega comieza vacía.

restaurant.addConstr(B_d[0] == 0)

#R8.Si no se va a comprar no pueden llegar insumos al restaurante

restaurant.addConstrs(I_d[d] <= k_d[d] * Q for d in Dias)

#R9.Los días domingo no se va a comprar.

for d in Dias:
    if (d+1)%7==0:
        restaurant.addConstr(I_d[d] == 0)
        restaurant.addConstr(k_d[d] <= I_d[d])

#R10.No se debe superar la capacidad máxima de almacenaje.

restaurant.addConstrs(v * B_d[d] <= V for d in Dias)

#R11.Cada trabajador puede trabajar en un turno por día como máximo

restaurant.addConstrs(quicksum(quicksum(T_nmhd[n,m,h,d] for m in M) for h in H) <= 1 for d in Dias for n in N)

#Función Objetivo

Ganancias = quicksum(quicksum(U * D_hd[d][h] * z_d[d] for h in H) for d in Dias)
Costos = A + B + quicksum(L_f + z_d[d] *(L_v - L_f) + k_d[d]*(C_k + C_i*I_d[d])   + quicksum(quicksum(z_d[d]* CT_m[m]*quicksum(T_nmhd[n,m,h,d] for n in N) for m in M) for h in H ) for d in Dias)
Objetivo = Ganancias - Costos

restaurant.setObjective(Objetivo, GRB.MAXIMIZE)

restaurant.update()

restaurant.optimize()


restaurant.printAttr("X")
print("\n-------------\n")

