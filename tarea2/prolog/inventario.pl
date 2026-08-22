% Declara el módulo y exporta las cuatro piezas que usa el backend.
% La aridad /1 identifica los hechos que reciben una lista; /1 también identifica
% el recorrido recursivo y /5 identifica la regla principal de procesamiento.
:- module(inventario_rpg, [
    inventario_principal/1,
    inventario_secundario/1,
    mostrar_inventario/1,
    procesar_inventario/5
]).

% Importa las implementaciones estándar de listas de SWI-Prolog.
% append/3, length/2, member/2, reverse/2, sort/2 y msort/2 quedan disponibles.
:- use_module(library(lists)).

% Hecho /1 con los objetos principales del aventurero.
% pocion_roja aparece dos veces para demostrar el comportamiento con duplicados.
inventario_principal([
    espada_larga,
    pocion_roja,
    pocion_roja,
    escudo_torre
]).

% Hecho /1 con cuatro objetos secundarios distintos del aventurero.
inventario_secundario([
    antorcha,
    mapa_antiguo,
    llave_plata,
    gema_lunar
]).

% Caso base de mostrar_inventario/1: una lista vacía ya fue recorrida por completo.
% format/2 imprime un mensaje y la regla termina satisfactoriamente.
mostrar_inventario([]) :-
    format('  [Prolog] Fin del recorrido recursivo.~n', []).

% Caso recursivo de mostrar_inventario/1: [Cabeza|Cola] separa el primer item
% de los restantes; format/2 muestra la Cabeza y la llamada recursiva procesa la Cola.
mostrar_inventario([Cabeza|Cola]) :-
    format('  [Prolog] Item: ~w~n', [Cabeza]),
    mostrar_inventario(Cola).

% procesar_inventario/5 recibe ItemBuscado y unifica cuatro salidas calculadas.
% El orden de las metas conserva la secuencia solicitada en la actividad:
% append/3, length/2, member/2, reverse/2, sort/2 y msort/2.
% La última meta ejecutable es mostrar_inventario/1 sobre InventarioGeneral.
procesar_inventario(
    ItemBuscado,
    TotalItems,
    InventarioInvertido,
    InventarioUnico,
    InventarioOrdenado
) :-
    % Obtiene la lista principal mediante el hecho inventario_principal/1.
    inventario_principal(ItemsPrincipales),
    % Obtiene la lista secundaria mediante el hecho inventario_secundario/1.
    inventario_secundario(ItemsSecundarios),
    % append/3 concatena ambas listas en InventarioGeneral.
    append(ItemsPrincipales, ItemsSecundarios, InventarioGeneral),
    % length/2 unifica TotalItems con la cantidad total de elementos.
    length(InventarioGeneral, TotalItems),
    % member/2 verifica por unificación que el item solicitado exista.
    member(ItemBuscado, InventarioGeneral),
    % reverse/2 unifica InventarioInvertido con el orden contrario.
    reverse(InventarioGeneral, InventarioInvertido),
    % sort/2 ordena y elimina duplicados para obtener InventarioUnico.
    sort(InventarioGeneral, InventarioUnico),
    % msort/2 ordena conservando los duplicados en InventarioOrdenado.
    msort(InventarioGeneral, InventarioOrdenado),
    % Anuncia la consulta antes del recorrido para que la consola sea verificable.
    format('~n[Prolog] Consulta exitosa para: ~w~n', [ItemBuscado]),
    % Esta es la última instrucción: imprime todo el inventario con recursividad.
    mostrar_inventario(InventarioGeneral).
