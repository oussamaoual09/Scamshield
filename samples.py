"""Exemples de messages de test pour ScamShield. Tous les contenus sont fictifs."""

# Chaque exemple : titre affiché, catégorie attendue (code), langue (fr, ar, darija, en) et texte
EXEMPLES = [
    {
        "titre": "Phishing : faux SMS Barid Bank",
        "categorie": "phishing",
        "langue": "fr",
        "texte": (
            "BARID BANK : Votre compte est suspendu suite à une activité inhabituelle. "
            "Pour le réactiver, confirmez votre identité dans les 24h sur http://baridbank-verif-client.com "
            "et saisissez le code OTP reçu par SMS. Dernier avis."
        ),
    },
    {
        "titre": "Phishing : e-mail CIH Bank (lien raccourci)",
        "categorie": "phishing",
        "langue": "fr",
        "texte": (
            "Objet : Alerte de sécurité CIH Bank\n\n"
            "Bonjour client,\n"
            "Une tentative de connexion suspecte a été détectée sur votre carte. "
            "Votre carte sera bloquée sous 24 heures. Cliquez ici : https://bit.ly/cih-secure-2026 "
            "et renseignez votre numéro de carte, la date d'expiration et le CVV pour la débloquer.\n"
            "Service sécurité CIH"
        ),
    },
    {
        "titre": "Phishing : SMS Barid Bank en arabe",
        "categorie": "phishing",
        "langue": "ar",
        "texte": (
            "عاجل: حسابك في بريد بنك معلق بسبب محاولة دخول مشبوهة. "
            "لإعادة تفعيله خلال 24 ساعة، أدخل رمز التحقق OTP الذي وصلك عبر الرسائل القصيرة "
            "على الرابط التالي: http://barid-bank-activation.xyz"
        ),
    },
    {
        "titre": "Faux placement : crypto sur WhatsApp",
        "categorie": "faux_placement",
        "langue": "fr",
        "texte": (
            "Bonjour, je suis conseiller en investissement. Notre plateforme crypto offre un rendement "
            "garanti de 15% par semaine, sans aucun risque. Déposez 500 € aujourd'hui et doublez votre "
            "argent en 7 jours. Rejoignez notre canal WhatsApp VIP pour les placements, les places sont "
            "limitées : répondez maintenant."
        ),
    },
    {
        "titre": "Faux placement : robot Forex sur Telegram",
        "categorie": "faux_placement",
        "langue": "fr",
        "texte": (
            "Notre robot de trading Forex génère 300% de gains par mois, soit 10% par jour selon nos clients ! "
            "Rendement garanti, zéro risque. Contactez-nous sur Telegram (@forexpro_gains) pour ouvrir votre "
            "compte. Dernière chance aujourd'hui."
        ),
    },
    {
        "titre": "Pyramide : marketing de réseau",
        "categorie": "ponzi",
        "langue": "fr",
        "texte": (
            "Devenez membre partenaire et gagnez des commissions sur vos filleuls ! Inscrivez-vous avec un "
            "pack d'entrée de 1 500 DH, recrutez 5 personnes et touchez des bonus sur tout votre réseau, "
            "niveau 1 à niveau 10. Parrainage illimité !"
        ),
    },
    {
        "titre": "Faux prêt : frais d'avance en darija",
        "categorie": "faux_pret",
        "langue": "darija",
        "texte": (
            "Salam, crédit express bla dmanat bla wraq, accord en 24h jusqu'à 200 000 DH. "
            "Ila bghiti flous, khlas les frais de dossier de 800 DH par Western Union avant le déblocage. "
            "Dir vite, l'offre expire aujourd'hui !"
        ),
    },
    {
        "titre": "Faux gain : loterie internationale",
        "categorie": "faux_gain",
        "langue": "fr",
        "texte": (
            "FÉLICITATIONS ! Vous avez gagné 1 000 000 € à la loterie internationale ! Pour débloquer votre "
            "gain, payez les frais de transfert de 300 € avant demain. Contactez notre bénéficiaire par e-mail "
            "et ne dites à personne ce tirage."
        ),
    },
    {
        "titre": "Autre : faux emploi à l'étranger",
        "categorie": "autre",
        "langue": "fr",
        "texte": (
            "Offre d'emploi urgente au Canada : poste de magasinier, salaire 3 500 $/mois, visa et billet "
            "d'avion offerts après paiement des frais d'inscription de 1 200 DH. Envoyez le paiement par "
            "Western Union, places limitées."
        ),
    },
    {
        "titre": "Message légitime : rappel de rendez-vous",
        "categorie": "sur",
        "langue": "fr",
        "texte": (
            "Bonjour Mme Alami, nous vous rappelons votre rendez-vous à la pharmacie Centrale demain à 10h. "
            "Pour toute modification, appelez directement la pharmacie. Bonne journée !"
        ),
    },
]
