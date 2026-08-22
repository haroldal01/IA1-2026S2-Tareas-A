from pyswip import Prolog

prolog = Prolog()

prolog.consult("auxiliar/auxiliar.pl")

print("El superior de ana es: ")
for result in prolog.query("superior(X, ana)"):
    print(result["X"])

print("Los companeros de ana son: ")
for result in prolog.query("companero(X, ana)"):
    print(result["X"])

print("carlos y juan son companeros: ")
result = list(prolog.query("companero(carlos, juan)"))
if result:
    print("Si")
else:
    print("No")
