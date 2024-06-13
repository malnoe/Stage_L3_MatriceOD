import scipy.optimize
import numpy as np
from bus import somme_colonne, somme_ligne


def affiche_matrice_propre(M):
    """
    Affiche la matrice M dans la console Python
    :param M:
    """
    # Déterminer la largeur maximale d'un élément du tableau pour l'alignement
    largeur_max = 6
    for ligne in M:
        # Joindre les éléments de la ligne avec un espace et les aligner à droite selon la largeur maximale
        ligne_formatee = " ".join(f"{str(round(item, 5)):>{largeur_max}}" for item in ligne)
        print(ligne_formatee)
    print('\n')
    return None


def normalisaiton_vecteurs(m, v):
    K = sum(m)
    normalized_m = [m_i / K for m_i in m]
    normalized_v = [v_i / K for v_i in v]
    return normalized_m, normalized_v


def generation_matrice_numeros(n):
    M = [[-1] * n for _ in range(n)]
    index = 0
    for i in range(0, n):
        for j in range(i + 1, n):
            M[i][j] = index
            index += 1
    return M


def vecteur_initial(m, v):
    n = len(m)
    d = int((n - 1) * n / 2)
    x0 = [0 for _ in range(d)]
    matrice_numeros = generation_matrice_numeros(n)
    for i in range(0, n - 1):
        for j in range(i + 1, n):
            index = matrice_numeros[i][j]
            x0[index] = m[i] * v[j]
    return x0


def initialise_matrice_from_vect(x, n):
    matrice = [[0] * n for _ in range(n)]
    index = 0
    for i in range(n):
        for j in range(i + 1, n):
            matrice[i][j] = x[index]
            index += 1
    return matrice


def qualite_resultat(vect_resultat, m, v):
    """
    :param vect_resultat: un vecteur avec les resultats d'une optimisation
    :param m: les montees (non-normalises)
    :param v: les descentes (non-normalises)
    :return: la qualite du resultat vis-a-vis du respect des contraintes
    """
    N = len(m)
    matrice_resultat = initialise_matrice_from_vect(vect_resultat, N)
    normalized_m, normalized_v = normalisaiton_vecteurs(m, v)
    dist = 0
    # Distance pour le respect des sommes sur les lignes et les colonnes
    for i in range(N):
        dist += (somme_ligne(matrice_resultat, i) - normalized_m[i]) ** 2 + (
                somme_colonne(matrice_resultat, i) - normalized_v[i]) ** 2

    # Distance pour le respect des valeurs >= 0
    for x_i in vect_resultat:
        if x_i < 0:
            dist += (x_i) ** 2
    return dist


# Methode Trust-Region Constrained Algorithm de Scipy

def generation_matrice_contraintes(n):
    d = int((n - 1) * n / 2)

    # Matrice numéros
    matrice_numeros = generation_matrice_numeros(n)

    # Matrice vierge pour les contraintes
    A = [[0] * d for _ in range(2 * n)]

    # Contraintes de montees
    for i in range(0, n):

        for j in range(1, n):
            temp_index = matrice_numeros[i][j]
            if temp_index != -1:
                A[i][temp_index] = 1

    # Contraintes de descentes
    ligne_descente = n
    for j in range(0, n):
        for i in range(0, n):
            temp_index = matrice_numeros[i][j]
            if temp_index != -1:
                A[ligne_descente + j][temp_index] = 1

    return A


def optimisation_scipy(m, v):
    n = len(m)
    d = int((n - 1) * n / 2)

    def entropie(x):
        res = 0
        # Entropie
        for x_i in x:
            if x_i > 0:
                res += x_i * np.log(x_i)
        return res

    # Contraintes sur les montees et descentes
    normalized_m, normalized_v = normalisaiton_vecteurs(m, v)
    montes_descentes = normalized_m + normalized_v
    matrice_contraintes = generation_matrice_contraintes(n)
    contraintes_montes_descentes = scipy.optimize.LinearConstraint(matrice_contraintes, montes_descentes,
                                                                   montes_descentes)

    # Contraintes sur les valeurs positives
    zeros = [0 for _ in range(4 * n)]
    bnds = [(0, None) for _ in range(d)]

    # Vecteur initial : produit des marginales
    x0 = vecteur_initial(normalized_m, normalized_v)

    # Minimisation par la méhtode de scipy
    resultat = scipy.optimize.minimize(entropie, x0, method='trust-constr', bounds=bnds,
                                       constraints=contraintes_montes_descentes)
    return resultat


def affichage_resultat_opti_scipy(m, v):
    resultat = optimisation_scipy(m, v)
    vect_resultat = resultat.x
    matrice_resultat = initialise_matrice_from_vect(vect_resultat, len(m))
    qual_resultat = qualite_resultat(vect_resultat, m, v)
    affiche_matrice_propre(matrice_resultat)
    print("La qualité du resultat est de :" + '\n' + str(qual_resultat))


# Methode de penalisaiton (algorithme personnel)


def penalisation(m, v, eps):
    """
    :param m: liste des montees (contrainte)
    :param v: liste des descentes (contrainite)
    :param eps: valeur de la penalisation
    :return: la matrice OD minimisant l'entropie par la methode de penalisation
    """
    n = len(m)
    inv_esp = 1 / eps
    normalized_m, normalized_v = normalisaiton_vecteurs(m, v)

    # Definition de la fonction a minimiser avec l'ajout des contraintes
    def entropie_et_contraintes(x):
        res = 0
        # Entropie
        for x_i in x:
            if x_i > 0:
                res += x_i * np.log(x_i)

        # Reconstituer la matrice pour faire les calculs sur les lignes et colonnes
        matrice = initialise_matrice_from_vect(x, n)

        # Contraintes sur les montees
        for i in range(n - 1):
            temp_sum = 0
            for j in range(i + 1, n):
                temp_sum += matrice[i][j]
            temp_sum += -normalized_m[i]
            res += inv_esp * temp_sum * temp_sum

        # Contraintes sur les descentes
        for j in range(1, n):
            temp_sum = 0
            for i in range(0, j):
                temp_sum += matrice[i][j]
            temp_sum += -normalized_v[j]
            res += inv_esp * temp_sum * temp_sum

        # Contraintes sur le caractère positif
        for x_i in x:
            res += max(-inv_esp * x_i, 0) ** 2

        return res

    # Fonction scipy
    x0 = vecteur_initial(normalized_m, normalized_v)
    resultat = scipy.optimize.minimize(entropie_et_contraintes, x0)

    return resultat


def variation_epsilon(m, d):
    res_trouve = True
    best_vector = []
    best_qualite = 100000
    eps = 0.1
    while res_trouve:
        eps = eps / 10
        resultat = penalisation(m, d, eps)
        res_trouve = resultat.success
        res_vector = resultat.x
        if res_trouve:
            qualite = qualite_resultat(res_vector, m, d)
            if qualite < best_qualite:
                best_qualite = qualite
                best_vector = res_vector
    return best_vector, best_qualite


testing = True
if testing:
    m5 = [2, 3, 1, 2, 0]
    v5 = [0, 1, 2, 2, 3]

    print("Variation epsilon vecteur 5")
    vect_res5, qualite_res5 = variation_epsilon(m5, v5)
    affiche_matrice_propre(initialise_matrice_from_vect(vect_res5, 5))
    print("La qualité du resultat est de : ")
    print(str(qualite_res5))
    print(" ")
    print("testing optimization from scipy method :" + '\n')
    affichage_resultat_opti_scipy(m5, v5)
    print("__________________________________________________________________________________________________________")
    m6 = [5, 4, 6, 3, 1, 0]
    v6 = [0, 2, 4, 3, 5, 5]
    print("Variation epsilon vecteur 6")
    vect_res6, qualite_res6 = variation_epsilon(m6, v6)
    affiche_matrice_propre(initialise_matrice_from_vect(vect_res6, 6))
    print("La qualité du resultat par la methode de penalisation est de : ")
    print(str(qualite_res6))
    print(" ")
    print("testing optimization from scipy method :" + '\n')
    affichage_resultat_opti_scipy(m6, v6)
