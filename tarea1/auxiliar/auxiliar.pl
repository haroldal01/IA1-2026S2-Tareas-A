% ------------- hechos ------------
jefe(juan, luis).
jefe(luis, ana).
jefe(luis, carlos).
amigo(ana, carlos).
amigo(carlos, ana).

% ------------- reglas -------------
superior(X, Y) :- jefe(X, Z), jefe(Z, Y).
companero(X, Y) :- jefe(Z, X), jefe(Z, Y).