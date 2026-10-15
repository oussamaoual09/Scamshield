"""Moteur de règles de ScamShield : détection heuristique des signaux d'arnaque, catalogue des types et fiches pédagogiques."""

import re
import unicodedata
from dataclasses import dataclass

# Catalogue des types d'arnaques : libellé complet, libellé court et icône d'affichage
CATEGORIES = {
    "phishing": {"libelle": "Phishing (faux SMS / e-mail de banque)", "court": "Phishing", "icone": "🎣"},
    "faux_placement": {"libelle": "Faux placement (Forex, crypto, rendement garanti)", "court": "Faux placement", "icone": "📈"},
    "ponzi": {"libelle": "Pyramide de Ponzi / marketing de réseau abusif", "court": "Pyramide / Ponzi", "icone": "🔺"},
    "faux_pret": {"libelle": "Faux prêt (frais à payer d'avance)", "court": "Faux prêt", "icone": "💸"},
    "faux_gain": {"libelle": "Faux gain (loterie, héritage)", "court": "Faux gain", "icone": "🎁"},
    "autre": {"libelle": "Autre / non classé", "court": "Autre", "icone": "❓"},
    "sur": {"libelle": "Aucune arnaque connue détectée", "court": "Aucune", "icone": "✅"},
}

# Types affichés sur le graphique radar (le type « autre » n'y figure pas)
CATEGORIES_RADAR = ["phishing", "faux_placement", "ponzi", "faux_pret", "faux_gain"]

# Niveaux de risque : code interne -> libellé affiché
NIVEAUX = {"sur": "Sûr", "suspect": "Suspect", "arnaque": "Arnaque probable"}

# Conseils par défaut, utilisés si l'IA n'est pas disponible
CONSEILS_PAR_TYPE = {
    "phishing": [
        "Ne cliquez sur aucun lien du message : ouvrez l'application ou tapez vous-même l'adresse officielle de votre banque.",
        "Ne communiquez jamais votre code OTP, votre mot de passe ni les données de votre carte.",
        "Appelez votre banque au numéro figurant au dos de votre carte ou sur son site officiel pour vérifier.",
    ],
    "faux_placement": [
        "Ne versez aucun argent sur une plateforme non vérifiée, surtout si elle promet un gain garanti.",
        "Vérifiez si l'intermédiaire est agréé par le régulateur de votre pays (AMMC au Maroc).",
        "Méfiez-vous des conseillers qui vous contactent sur WhatsApp ou Telegram et qui pressent de décider.",
    ],
    "ponzi": [
        "Ne payez aucune adhésion ni pack d'entrée pour gagner de l'argent grâce au recrutement.",
        "Un gain qui dépend du nombre de personnes recrutées relève d'une pyramide : quittez le projet.",
        "Demandez les statuts, l'agrément et l'origine réelle des revenus avant de confier le moindre dirham.",
    ],
    "faux_pret": [
        "Ne payez jamais de frais de dossier, d'assurance ou de déblocage avant d'avoir reçu un prêt.",
        "Un établissement de crédit sérieux demande un dossier complet et vérifie votre situation.",
        "Refusez les paiements par carte cadeau, Western Union ou crypto-monnaie.",
    ],
    "faux_gain": [
        "Vous ne pouvez pas gagner à une loterie à laquelle vous n'avez pas participé.",
        "Ne payez jamais de frais pour « débloquer » un gain ou un héritage.",
        "Ne répondez pas et ne transmettez aucune donnée personnelle ou bancaire.",
    ],
    "autre": [
        "Ne transférez pas d'argent à une personne que vous ne connaissez pas, même sous pression.",
        "Prenez le temps de vérifier auprès d'une source officielle avant toute décision.",
        "Parlez-en à un proche : un regard extérieur aide souvent à repérer l'arnaque.",
    ],
    "sur": [
        "Aucun signal d'arnaque connu n'a été repéré, mais restez vigilant avec les liens et les demandes d'argent.",
        "En cas de doute, vérifiez toujours l'expéditeur via un canal officiel.",
    ],
}

# Conseils ajoutés lorsque le niveau est Suspect ou Arnaque probable
CONSEILS_GENERAUX = [
    "Ne payez aucun frais avant d'avoir vérifié l'interlocuteur.",
    "Conservez les messages comme preuves et signalez-les aux autorités compétentes.",
]

# Fiches pédagogiques affichées dans l'onglet « Apprendre »
FICHES_PEDAGOGIQUES = {
    "phishing": {
        "fonctionnement": "L'arnaqueur se fait passer pour votre banque, un opérateur ou une administration (Barid Bank, CIH, Attijariwafa, Inwi, CNSS, DGI…). Il envoie un SMS ou un e-mail alarmant avec un lien vers une fausse page qui copie le vrai site. Son but : voler vos identifiants, votre code OTP ou les données de votre carte.",
        "signes": [
            "Urgence : « votre compte sera bloqué dans 24h »",
            "Demande de code OTP, de mot de passe ou de numéro de carte",
            "Lien raccourci, ou adresse qui imite la banque (tirets, chiffres, extension inhabituelle)",
            "Formule générique (« Cher client ») et fautes d'orthographe",
        ],
        "exemple": "« BARID BANK : votre compte est suspendu. Confirmez votre identité sur http://bank-verif-client.xyz et saisissez le code reçu par SMS. »",
        "que_faire": [
            "Ne cliquez sur rien et ne répondez pas.",
            "Connectez-vous à votre banque via son application officielle, ou tapez son adresse vous-même.",
            "Si vous avez transmis un code ou un mot de passe : changez-les immédiatement et prévenez votre banque.",
            "Signalez le message à votre banque et aux autorités.",
        ],
    },
    "faux_placement": {
        "fonctionnement": "On vous promet des gains rapides et sans risque grâce au Forex, aux crypto-monnaies ou à un « robot de trading ». Vous versez de l'argent sur une plateforme qui affiche de faux gains. Quand vous voulez retirer, on vous demande de payer des taxes, ou on vous bloque l'accès.",
        "signes": [
            "Rendement garanti ou « zéro risque »",
            "Rendements irréalistes : 10 % par jour, gains multipliés par 10 en quelques jours",
            "Contact et « conseiller » via WhatsApp ou Telegram",
            "Plateforme non agréée et pression pour déposer vite",
        ],
        "exemple": "« Notre robot Forex génère 300 % de gains par mois, zéro risque. Rejoignez notre canal Telegram VIP avant ce soir. »",
        "que_faire": [
            "Ne versez aucun dépôt sur une plateforme inconnue.",
            "Vérifiez l'agrément de l'intermédiaire auprès du régulateur (AMMC au Maroc).",
            "Méfiez-vous de tout retrait conditionné à un nouveau paiement.",
            "Si vous avez déjà versé de l'argent : conservez les preuves, prévenez votre banque et portez plainte.",
        ],
    },
    "ponzi": {
        "fonctionnement": "Une pyramide rémunère les anciens membres avec l'argent des nouveaux, et non avec de vrais bénéfices. Le système s'effondre dès que les recrues ne suffisent plus. Le marketing de réseau abusif lui ressemble : on y gagne surtout en recrutant.",
        "signes": [
            "Gains liés au recrutement de nouveaux membres",
            "Adhésion ou « pack d'entrée » payant et obligatoire",
            "Commissions sur plusieurs niveaux de filleuls",
            "Promesse de revenus réguliers sans produit réel ni vente",
        ],
        "exemple": "« Devenez partenaire, payez votre pack de 1 500 DH, recrutez 5 personnes et touchez des bonus sur tout votre réseau. »",
        "que_faire": [
            "N'adhérez pas et ne payez aucun pack d'entrée.",
            "Ne recrutez personne : vous entraîneriez vos proches dans la perte.",
            "Demandez les statuts, l'agrément et l'origine réelle des revenus.",
            "Si vous êtes déjà engagé : arrêtez de payer et signalez l'entreprise aux autorités.",
        ],
    },
    "faux_pret": {
        "fonctionnement": "Un faux organisme de crédit promet un prêt rapide, sans justificatif et à taux attractif. Une fois l'offre acceptée, on vous demande de payer des frais (dossier, assurance, déblocage) avant le versement. Le prêt n'arrive jamais.",
        "signes": [
            "Prêt accordé sans dossier, sans garant et sans vérification",
            "Frais à payer d'avance pour débloquer le montant",
            "Paiement par carte cadeau, Western Union, mandat ou crypto-monnaie",
            "Offre à durée très courte : « expire aujourd'hui »",
        ],
        "exemple": "« Crédit express sans justificatif jusqu'à 200 000 DH. Payez 800 DH de frais de dossier avant le déblocage. »",
        "que_faire": [
            "Ne payez jamais de frais avant d'avoir reçu le prêt.",
            "Ne communiquez pas les données de votre carte ni vos identifiants bancaires.",
            "Adressez-vous directement à votre banque ou à un établissement de crédit agréé.",
            "Signalez l'offre aux autorités compétentes.",
        ],
    },
    "faux_gain": {
        "fonctionnement": "Vous êtes « sélectionné » pour une loterie, un concours ou un héritage que vous n'avez jamais réclamé. Pour toucher le gain, on vous demande de payer des frais de transfert ou des taxes, puis de garder le secret. L'argent promis n'existe pas.",
        "signes": [
            "Gain à une loterie à laquelle vous n'avez jamais participé",
            "Héritage d'un inconnu ou fonds « bloqués » à débloquer",
            "Frais de transfert, taxes ou assurance à payer d'avance",
            "Consigne de garder le secret ou de ne pas en parler à votre banque",
        ],
        "exemple": "« Félicitations ! Vous avez gagné 1 000 000 € à la loterie. Payez 300 € de frais de transfert et ne dites à personne. »",
        "que_faire": [
            "Ne répondez pas et ne payez aucun frais.",
            "Une vraie loterie ne demande jamais d'argent pour verser un gain.",
            "Parlez-en à un proche ou à votre banque avant toute action.",
            "Signalez le message aux autorités.",
        ],
    },
    "autre": {
        "fonctionnement": "Ce sont les arnaques qui n'entrent dans aucune catégorie précise : fausses offres d'emploi à l'étranger avec frais d'inscription, faux conseillers qui menacent de poursuites, faux proches en détresse qui demandent de l'argent, ou demandes de paiement inhabituelles.",
        "signes": [
            "Pression émotionnelle : peur, urgence ou affection",
            "Menace de sanction judiciaire ou d'arrestation",
            "Paiement exigé par carte cadeau, virement ou mandat",
            "Demande de garder le secret",
        ],
        "exemple": "« Offre d'emploi au Canada : payez 1 200 DH de frais d'inscription par Western Union, places limitées. »",
        "que_faire": [
            "Coupez le contact et ne payez rien.",
            "Vérifiez directement auprès de la personne ou de l'organisme, avec un numéro que vous connaissez déjà.",
            "Ne transférez jamais d'argent sous la pression.",
            "Signalez l'arnaque aux autorités et à votre banque.",
        ],
    },
}

# Nombre maximal d'extraits de texte affichés par règle
MAX_MOTS = 3

# Marques marocaines (banques, opérateurs, administrations) souvent imitées
MARQUES_LATIN = r"\b(?:barid ?bank|barid al ?maghrib|cih ?bank|cih|attijari ?wafa ?bank|attijariwafa|attijari|bank of africa|bmce|inwi|orange maroc|maroc ?telecom|cnss|dgi|direction generale des impots)\b"
MARQUES_ARABES = r"بريد ?بنك|التجاري ?وفا|بنك ?افريقيا|اتصالات ?المغرب|اينوي|الضمان الاجتماعي|المديرية العامة للضرائب"
# Mots d'urgence ou de demande de données qui, associés à une marque, signalent un faux message
CONTEXTE_LATIN = r"\b(urgent\w*|immediatement|suspendu|bloque|desactive|otp|code|mot de passe|verifi\w*|mise a jour|cliquez|lien|24 ?h|confirm\w*|reactiver|activer|dernier avis|rembours\w*|colis)\b"
CONTEXTE_ARABE = r"معلق|موقوف|محجوز|عاجل|رمز|كود|الرابط|فورا|تحقق|تفعيل|تاكيد|استرداد"


@dataclass(frozen=True)
class Regle:
    """Règle de détection : nom, catégorie d'arnaque, poids en points, motifs regex et explication."""

    nom: str
    categorie: str
    poids: int
    motifs: tuple
    explication: str
    contexte: tuple = ()


REGLES = (
    Regle(
        nom="Urgence et pression temporelle",
        categorie="autre",
        poids=12,
        motifs=(
            r"\burgent\w*",
            r"\bimmediatement\b",
            r"\bdernier (avis|rappel)\b",
            r"\bderniere chance\b",
            r"\b(dans|sous) (les )?24 ?(h|heures?)\b",
            r"\bexpire[rz]? (aujourd'hui|bientot|ce soir|demain)\b",
            r"\bavant (minuit|ce soir)\b",
            r"\bplaces? limitees?\b",
            r"\bdaba\b|\bdork\b",
            r"عاجل|فورا|\bالان\b",
        ),
        explication="Le message met la pression avec une échéance très courte. Les arnaqueurs veulent vous empêcher de réfléchir.",
    ),
    Regle(
        nom="Compte ou carte bloqué(e)",
        categorie="phishing",
        poids=20,
        motifs=(
            r"\bcompte (a ete |est |sera |va etre )?(suspendu|bloque|desactive|restreint|verrouille|limite|cloture|ferme)\b",
            r"\bcarte (a ete |est |sera )?(bloquee|suspendue|desactivee|restreinte)\b",
            r"\bacces (restreint|bloque|suspendu|limite)\b",
            r"\b(votre|vos) (acces|comptes?|cartes?)\b.{0,25}\b(suspendu|bloque|restreint|limite|desactive)",
            r"(حساب|بطاقة).{0,30}(معلق|موقوف|محجوز|مغلق|محظور|مجمد)",
        ),
        explication="Le message annonce un compte ou une carte bloqués pour pousser à agir vite. C'est le scénario le plus courant du phishing bancaire.",
    ),
    Regle(
        nom="Demande de code OTP",
        categorie="phishing",
        poids=30,
        motifs=(
            r"\botp\b",
            r"\bcode (de )?(verification|securite|confidentiel|secret|sms|d'activation|d'acces|pin)\b",
            r"(رمز|كود|الرمز|الكود) ?(التحقق|التفعيل|السري|الخاص)",
        ),
        explication="Le message demande un code OTP ou de vérification. Aucune banque ni aucun service officiel ne demande ce code par SMS, téléphone ou lien.",
    ),
    Regle(
        nom="Demande de mot de passe",
        categorie="phishing",
        poids=30,
        motifs=(
            r"\bmot de passe\b|\bmdp\b|\bpassword\b",
            r"كلمة (السر|المرور)|الرقم السري",
        ),
        explication="Le message réclame un mot de passe. Un organisme sérieux ne vous demande jamais votre mot de passe.",
    ),
    Regle(
        nom="Demande de données de carte ou de compte",
        categorie="phishing",
        poids=35,
        motifs=(
            r"\bnumero (de |de la |de votre |du )?carte\b",
            r"\bcvv2?\b|\bcvc\b|\bcryptogramme\b",
            r"\bdate d'expiration\b",
            r"\brib\b|\biban\b",
            r"\bcode pin\b|\bcode secret de (votre )?carte\b",
            r"\bidentifiants? bancaires?\b",
            r"(رقم|ارقام) (البطاقة|بطاقتك|الحساب|الحساب البنكي)",
        ),
        explication="Le message demande des données de carte ou de compte (numéro de carte, CVV, RIB, IBAN). Ces informations permettent de vider un compte.",
    ),
    Regle(
        nom="Confirmation d'informations personnelles",
        categorie="phishing",
        poids=20,
        motifs=(
            r"\bconfirmez? (vos|tes|votre) (informations|coordonnees|donnees|identifiants|identite)\b",
            r"\b(mettre a jour|mise a jour|valider|verifiez?|verifier)\b.{0,25}\b(vos|votre|tes) (informations|coordonnees|donnees|identite|compte|dossier)\b",
            r"\b(confirm|verify|update) your (account|details|information|identity|password)\b",
            r"(تاكيد|تحديث|تحقق من) (معلوماتك|بياناتك|هويتك)",
        ),
        explication="Le message demande de confirmer ou de mettre à jour vos informations personnelles via un lien. C'est une technique classique de vol d'identité.",
    ),
    Regle(
        nom="Lien raccourci",
        categorie="phishing",
        poids=20,
        motifs=(
            r"\b(?:bit\.ly|tinyurl\.com|goo\.gl|cutt\.ly|rb\.gy|is\.gd|ow\.ly|shorturl\.at|t\.ly|tiny\.cc|bl\.ink|v\.gd|t\.co|s\.id)\b",
        ),
        explication="Le lien est raccourci : impossible de voir où il mène avant de cliquer. Les arnaqueurs s'en servent pour cacher de faux sites.",
    ),
    Regle(
        nom="Domaine imitant une banque ou un opérateur",
        categorie="phishing",
        poids=25,
        motifs=(
            r"\b[a-z0-9-]*(?:barid|cih|attijari|bankofafrica|bmce|maroctelecom|inwi|orangemaroc)[a-z0-9-]*\.(?!ma\b)[a-z]{2,}\b",
        ),
        explication="Le nom d'une banque ou d'un opérateur marocain apparaît dans un domaine qui ne se termine pas par .ma. Vérifiez l'adresse officielle : un tiret ou une lettre changés suffisent à tromper.",
    ),
    Regle(
        nom="Domaine à tirets ou chiffres inhabituels",
        categorie="phishing",
        poids=12,
        motifs=(
            r"\b[a-z]{2,}[-0-9][a-z0-9-]*\.(?:com|net|org|info|xyz|top|site|online|club|shop|buzz|icu|live|ma|fr|co|cc|tk|ga|ml|cf|gq|link|click)\b",
        ),
        explication="Le nom de domaine contient des tirets ou des chiffres de façon inhabituelle (par exemple « cih-secure2 »). C'est une technique de faux site.",
    ),
    Regle(
        nom="Extension de domaine à risque",
        categorie="phishing",
        poids=10,
        motifs=(
            r"\.(?:xyz|top|tk|ml|ga|cf|gq|buzz|icu|click|link|zip|mov|rest|cam|monster)\b",
        ),
        explication="Le site utilise une extension souvent employée pour des sites frauduleux (par exemple .xyz, .top ou .tk).",
    ),
    Regle(
        nom="Lien vers une adresse IP",
        categorie="phishing",
        poids=25,
        motifs=(
            r"https?://\d{1,3}(?:\.\d{1,3}){3}",
        ),
        explication="Le lien pointe directement vers une adresse IP au lieu d'un nom de site. C'est très rarement légitime.",
    ),
    Regle(
        nom="Invitation à cliquer",
        categorie="phishing",
        poids=8,
        motifs=(
            r"\bcliqu(ez|er) (sur |ici|ci dessous|sur ce)",
            r"\bclick (here|on)\b",
            r"\bاضغط (هنا|على)\b",
        ),
        explication="Le message vous invite à cliquer sur un lien. C'est parfois légitime, mais combiné à une urgence ou à une demande de données, c'est un signal d'alerte.",
    ),
    Regle(
        nom="Fausse alerte de sécurité",
        categorie="phishing",
        poids=15,
        motifs=(
            r"\b(activite|transaction|connexion|tentative|operation) (suspecte|inhabituelle|non autorisee|frauduleuse|anormale)\b",
            r"\b(alerte|avis) de securite\b",
            r"\b(virement|retrait|paiement|transaction) (suspect|non autorise|inhabituel|frauduleux)\b",
            r"\bsuspicious (activity|login|transaction)\b|\bunauthori[sz]ed (transaction|access|login)\b",
            r"(عملية|معاملة|محاولة) (مشبوهة|غير معتادة|غير مصرح بها)",
        ),
        explication="Le message signale une activité anormale sur votre compte pour créer la panique. Une banque ne vous demande jamais de valider une opération via un lien.",
    ),
    Regle(
        nom="Faux remboursement, amende ou colis bloqué",
        categorie="phishing",
        poids=12,
        motifs=(
            r"\brembours\w*",
            r"\bamende\b",
            r"\bcolis (bloque|en attente|retenu|non livre)",
            r"\bdroits? de douane\b|\bfrais de douane\b",
            r"\bfrais de livraison\b",
            r"استرداد|استرجاع|غرامة",
        ),
        explication="Le message promet un remboursement, annonce une amende ou un colis bloqué pour obtenir vos données ou un petit paiement. Ces faux prétextes sont très fréquents.",
    ),
    Regle(
        nom="Faux conseiller bancaire",
        categorie="phishing",
        poids=15,
        motifs=(
            r"\bje suis (votre |le |la )?(conseill\w*|agent|gestionnaire|technicien|responsable) (de |du |de la )?(votre )?(banque|service client|service fraude|service securite|securite|fraude|bmce|cih|barid|attijari|inwi|orange)\b",
        ),
        explication="Une personne se présente comme conseiller ou agent de votre banque ou d'un opérateur. Raccrochez et rappelez le numéro officiel.",
    ),
    Regle(
        nom="Marque marocaine citée avec urgence ou demande de données",
        categorie="phishing",
        poids=25,
        motifs=(MARQUES_LATIN, MARQUES_ARABES),
        explication="Une banque, un opérateur ou une administration marocaine est cité avec un ton d'urgence ou une demande de données. C'est le scénario type d'un faux message officiel.",
        contexte=(CONTEXTE_LATIN, CONTEXTE_ARABE),
    ),
    Regle(
        nom="Marque marocaine citée",
        categorie="phishing",
        poids=8,
        motifs=(MARQUES_LATIN, MARQUES_ARABES),
        explication="Une marque marocaine est citée. Vérifiez toujours l'expéditeur sur le site ou l'application officiels : citer une marque ne prouve rien à lui seul.",
    ),
    Regle(
        nom="Demande de garder le secret",
        categorie="autre",
        poids=15,
        motifs=(
            r"(?:\bne|\bn')\s?(?:le |la |en |les )?(?:dites?|parlez?)\s+(?:a\s+)?personne",
            r"\bgardez (ce |cela |ca )?secret\b",
            r"لا (تخبر|تخبري) (احدا|احد)",
        ),
        explication="Le message demande de garder le secret ou de ne parler à personne. C'est un moyen d'isoler la victime.",
    ),
    Regle(
        nom="Mode de paiement inhabituel",
        categorie="autre",
        poids=20,
        motifs=(
            r"\bcartes? (cadeaux?|itunes|google play|steam|psn|ps4|ps5|xbox|amazon)\b",
            r"\bwestern union\b|\bmoneygram\b|\bria money\b|\bmoney ?gram\b",
            r"\b(envoyez|virez|transferez|payez)\b.{0,30}\b(bitcoin|btc|usdt|cryptomonnaies?|crypto|cartes? cadeaux?)\b",
            r"ويسترن يونيون|ويسترن يونين",
        ),
        explication="Le paiement demandé (carte cadeau, Western Union, crypto-monnaie) est quasiment impossible à annuler. C'est un mode de paiement typique des arnaques.",
    ),
    Regle(
        nom="Contact par WhatsApp ou Telegram pour investir",
        categorie="faux_placement",
        poids=20,
        motifs=(
            r"\b(whatsapp|telegram)\b.{0,80}\b(invest\w*|placements?|gains?|trading|rendements?|profits?|capital|bots?|canal|euros?|dollars?|dh|dirhams?|usdt|btc)\b",
            r"\b(invest\w*|placements?|gains?|trading|rendements?|profits?|capital|bots?|canal)\b.{0,80}\b(whatsapp|telegram)\b",
            r"(واتساب|تيليجرام).{0,80}(استثمار|ربح|ارباح|تداول|راس المال)",
        ),
        explication="Un contact par messagerie (WhatsApp, Telegram) est proposé pour investir. Les établissements financiers sérieux ne sollicitent pas leurs clients ainsi.",
    ),
    Regle(
        nom="Rendement garanti ou sans risque",
        categorie="faux_placement",
        poids=35,
        motifs=(
            r"\brendements? (garantis?|assures?|certains?|fixes?)\b",
            r"\bgains? (garantis?|assures?|certains?)\b",
            r"\bsans (aucun )?risques?\b",
            r"\brisques? (zero|nul|0)\b|\bzero risques?\b",
            r"\bcapital (garanti|assure|protege)\b",
            r"\b100 ?% (garanti|sur|securise|assure)\b",
            r"\b(guaranteed|guarantee) (return|profit|income|gains?)s?\b|\brisk[- ]free\b|\bno risk\b|\bzero risk\b",
            r"\bgarantis?\w* a \d+ ?%",
            r"ارباح مضمونة|ربح مضمون|بدون مخاطر|بلا مخاطر|عائد مضمون",
        ),
        explication="Le message promet un rendement garanti ou sans risque. Aucun placement réel ne garantit des gains : c'est la promesse la plus typique des faux placements.",
    ),
    Regle(
        nom="Promesse de doubler son argent",
        categorie="faux_placement",
        poids=35,
        motifs=(
            r"\bdoubl(ez|er|e|ement) (votre|vos|ton|ta|le) (argent|mise|capital|investissement|placement)\b",
            r"\b(double|multiply|triple) your (money|investment)\b",
            r"\bx ?(10|20|50|100)\b",
            r"ضاعف\w* ا?موال|ضاعف\w* (استثمارك|ارباحك)",
        ),
        explication="Le message promet de multiplier votre argent (doublement, x10…). Une telle multiplication rapide n'existe pas dans les placements réels.",
    ),
    Regle(
        nom="Rendement irréaliste",
        categorie="faux_placement",
        poids=30,
        motifs=(
            r"\b\d{1,3}(?:[.,]\d{1,2})? ?% ?(?:a la|a|par|per|every|chaque|/) ?(?:jour|semaine|mois|day|week|month|heure|hour)s?\b",
            r"\b\d{1,3}(?:[.,]\d{1,2})? ?% (?:de |du |d')?(?:rendements?|gains?|benefices?|profits?|retours?|revenus?)\b.{0,25}\b(?:par|chaque|a la|per|every)\b",
            r"\b\d{1,3}(?:[.,]\d{1,2})? ?% ?(?:daily|weekly|monthly|a day|a week|a month|per day|per week|per month)\b",
        ),
        explication="Le rendement annoncé (par exemple « 10 % par jour ») est irréaliste. Même les meilleurs placements ne rapportent pas de tels montants de façon régulière.",
    ),
    Regle(
        nom="Forex, crypto ou trading",
        categorie="faux_placement",
        poids=10,
        motifs=(
            r"\b(forex|cryptos?|cryptomonnaies?|bitcoins?|btc|usdt|trading|traders?|binance|ethereum|bot de trading|robot de trading)\b",
            r"فوركس|كريبتو|بيتكوين|تداول",
        ),
        explication="Le message parle de Forex, de crypto-monnaies ou de trading. Ces marchés sont très risqués et servent souvent d'appâts. Ce mot seul ne prouve rien.",
    ),
    Regle(
        nom="Gains rapides ou revenus faciles",
        categorie="faux_placement",
        poids=15,
        motifs=(
            r"\bgains? (rapides?|faciles?|immediats?|express)\b",
            r"\b(revenus?|argent) (passifs?|facile|faciles|sans effort)\b|\bsans effort\b",
            r"\bdevenez riches?\b|\bdevenir riche\b",
            r"\bgagnez? \d+ ?(?:dh|mad|euros?|eur|€|dollars?|usd|\$|dirhams?) (?:par|chaque|en)\b",
            r"\bflous? (sahel|rapide|facile)\b|\bbla khedma\b|\bbla khdma\b",
            r"الربح السريع|ربح سريع|بدون مجهود",
        ),
        explication="Le message vante des gains rapides ou des revenus faciles. Plus une promesse de gain est rapide et simple, plus elle est souvent fausse.",
    ),
    Regle(
        nom="Plateforme non régulée",
        categorie="faux_placement",
        poids=15,
        motifs=(
            r"\bnon (regulee?|agree|autorisee?|supervisee?)\b",
            r"\bsans (agrement|licence|autorisation|regulation)\b",
            r"غير (مرخص|منظم)",
        ),
        explication="La plateforme ou l'intermédiaire n'est pas présenté comme agréé. Vérifiez l'agrément auprès de l'AMMC (Maroc) ou du régulateur financier de votre pays.",
    ),
    Regle(
        nom="Recrutement et parrainage",
        categorie="ponzi",
        poids=30,
        motifs=(
            r"\brecrutez\b",
            r"\bparrainages?\b|\bparrainez\b",
            r"\bdevenez (membres?|partenaires?|ambassadeurs?|distributeurs?)\b",
            r"\bfilleuls?\b",
            r"\bmlm\b|\bmulti ?level\b|\bpyramide\b",
            r"\bmarketing (de|a) reseau\b|\bmultiniveaux?\b|\bmulti niveaux?\b",
            r"\brecrutement de (nouveaux )?(membres|partenaires|personnes)\b",
            r"استقطاب|تجنيد|دعوة (الاصدقاء|الاشخاص|اشخاص)",
        ),
        explication="Le gain dépend du recrutement de nouvelles personnes. C'est la mécanique des pyramides de Ponzi et du marketing de réseau abusif : le système s'effondre quand les recrues manquent.",
    ),
    Regle(
        nom="Commissions sur le réseau",
        categorie="ponzi",
        poids=25,
        motifs=(
            r"\bcommissions? (sur|de|pour) (chaque |vos |tes |les |tous )?(filleuls?|recrues?|membres?|equipe|reseau|parrainages?|personnes|niveaux?)\b",
            r"\b(gains?|revenus?|bonus|primes?) (sur|grace a|grace aux|via) (vos |tes |les )?(filleuls?|reseau|equipe|recrues?|parrainages?)\b",
            r"\bniveau \d+\b.{0,40}\b(commissions?|bonus|gains?|pourcentages?)\b",
            r"عمولات?.{0,30}(اعضاء|شبكة|فريق|اصدقاء)",
        ),
        explication="Des commissions sont promises sur les personnes que vous recrutez, parfois sur plusieurs niveaux. C'est le cœur d'une pyramide.",
    ),
    Regle(
        nom="Adhésion ou pack d'entrée payant",
        categorie="ponzi",
        poids=25,
        motifs=(
            r"\b(pack|kit|ticket) (d'|de )?(entree|demarrage|depart|activation|adhesion)\b",
            r"\badhesion (payante|obligatoire|de \d+)\b|\badhesion a \d+",
            r"\b(payez|versez|investissez|depositez) (votre )?(adhesion|inscription|pack|ticket|kit)\b",
            r"دفع (رسوم|اشتراك) (الانضمام|التسجيل)",
        ),
        explication="Une adhésion ou un pack d'entrée payant est exigé pour commencer. Dans une pyramide, c'est souvent la vraie source de revenus des organisateurs.",
    ),
    Regle(
        nom="Frais à payer d'avance",
        categorie="faux_pret",
        poids=35,
        motifs=(
            r"\b(payez|payer|verser|versez|envoyez|envoyer|transferez|virez) .{0,40}\b(frais|avance|pour (debloquer|recevoir|obtenir|liberer|activer|retirer))\b",
            r"\b(frais|taxe|assurance|caution) (a payer|d'avance|avant (le |la )?(deblocage|decaissement|versement|virement|retrait))\b",
            r"\bfrais (de )?transfert\b",
            r"\bpayez? (d'avance|avant)\b",
            r"\bavant (le |la )?deblocage\b",
            r"\bavant (le |la )?(deblocage|decaissement|versement) (des |du |de )?(fonds|pret|credit|montant|somme|argent|gain)\b",
            r"\bpour (debloquer|liberer|recuperer|activer) (votre |vos |le |la |les )?(gain|prix|lot|pret|credit|fonds|heritage|argent|colis)\b",
            r"ادفع (مقدما|مسبقا)|قبل (صرف|تحويل) (القرض|المبلغ)",
        ),
        explication="Vous devez payer avant de recevoir un gain ou un prêt. Un vrai prêt ou un vrai gain ne demande jamais d'argent d'avance.",
    ),
    Regle(
        nom="Frais de dossier ou de transfert",
        categorie="faux_pret",
        poids=25,
        motifs=(
            r"\bfrais (de |d')?(dossier|traitement|deblocage|decaissement|assurance|notaire|garantie|gestion|timbre|douane|enregistrement)\b",
            r"(رسوم|مصاريف) (الملف|التحويل|المعالجة)",
        ),
        explication="Des frais de dossier ou de transfert sont réclamés. Demandez le détail écrit des frais et refusez tout paiement par carte cadeau, mandat ou Western Union.",
    ),
    Regle(
        nom="Prêt accordé sans conditions",
        categorie="faux_pret",
        poids=20,
        motifs=(
            r"\bpret (accorde|approuve|disponible|garanti|express|rapide|immediat|instantane)\b",
            r"\bcredit (express|rapide|immediat|instantane|sans condition)s?\b",
            r"\bsans (justificatif|garant|verification|enquete|consultation|fiche de paie|cdi|aucun document)s?\b",
            r"\bbla (dmanat|wraq|ta7qiq|ta9qiq)\b",
            r"\bbghiti? (flous?|dirhams?|fluss)\b",
            r"قرض (فوري|سريع)|بدون (ضمانات|ضامن|كفيل)|بلا (ضمانات|ضامن)",
        ),
        explication="Le prêt est accordé sans conditions ni vérification. Un établissement de crédit contrôle toujours votre situation : l'absence de contrôle est un signal d'arnaque.",
    ),
    Regle(
        nom="Annonce de gain inattendu",
        categorie="faux_gain",
        poids=30,
        motifs=(
            r"\bvous (avez |etes |es )?(ete )?(gagne|remporte|selectionne|tire)s?\b",
            r"\bfelicitations?\b.{0,50}\b(gagn\w*|prix|lot|remport\w*|selection\w*|tire|heritage|cadeau|jackpot|montant)\b",
            r"\byou(?:'ve| have| are)? (?:won|been selected|been chosen)\b|\byou are (the )?winners?\b",
            r"فزت|مبروك.{0,40}(ربحت|جائزة|الجائزة)|ربحت (جائزة|مبلغ)",
        ),
        explication="Le message annonce un gain, une sélection ou une récompense que vous n'avez pas demandés. Les faux gains servent à obtenir de l'argent ou des données.",
    ),
    Regle(
        nom="Loterie",
        categorie="faux_gain",
        poids=30,
        motifs=(
            r"\bloterie\b|\blottery\b|\bloto\b|\bjackpot\b|\btirage au sort\b",
            r"يانصيب|قرعة|الجائزة الكبرى|جائزة كبرى",
        ),
        explication="Une loterie est évoquée. Vous ne pouvez pas gagner à un tirage auquel vous n'avez pas participé, et aucun gain réel n'exige de frais.",
    ),
    Regle(
        nom="Héritage ou fonds bloqués",
        categorie="faux_gain",
        poids=30,
        motifs=(
            r"\bheritages?\b|\bheritiers?\b|\bheritieres?\b",
            r"\bdefunt\w*|\bdecede\w*|\bfeu (mon|votre|ton|notre) (pere|oncle|mari|epoux|frere|grand)",
            r"\bfonds? (bloques?|en attente|dormants?)\b|\bavoirs? (non reclames?|dormants?)\b|\bcomptes? (dormants?|en desherence)\b",
            r"المتوف\w*|المرحوم\w*|ميراث|ورثة|التركة",
        ),
        explication="Un héritage, un défunt ou des fonds bloqués sont évoqués. Ces histoires servent à vous faire avancer des frais pour toucher une somme qui n'existe pas.",
    ),
    Regle(
        nom="Statut de bénéficiaire d'une somme",
        categorie="faux_gain",
        poids=20,
        motifs=(
            r"\bvous (etes|es) (le |la )?beneficiaires?\b",
            r"\bbeneficiaires? (d'une|d'un|de la|de l'|de) (somme|prix|lot|fonds|capital|million\w*|heritage)\b",
            r"\bbeneficiaire\b.{0,40}\b(millions?|usd|dollars?|euros?|€|\$)\b",
        ),
        explication="Vous êtes présenté comme bénéficiaire d'une somme importante. Un inconnu qui vous offre de l'argent demande presque toujours des frais en échange.",
    ),
    Regle(
        nom="Menace de poursuites ou d'arrestation",
        categorie="autre",
        poids=25,
        motifs=(
            r"\b(arrestation|mandat d'arret|poursuites? judiciaires?|huissier|police judiciaire|dossier judiciaire|casier judiciaire|tribunal)\b",
            r"\b(vous serez|vous allez etre|sera) (arrete|poursuivi|sanctionne|condamne)\w*\b",
            r"اعتقال|محكمة|الشرطة القضائية|متابعة قضائية|استدعاء قضائي",
        ),
        explication="Le message menace de poursuites, d'arrestation ou de sanctions pour obtenir une réaction immédiate. Les autorités ne réclament pas d'argent par SMS ou messagerie.",
    ),
    Regle(
        nom="Offre d'emploi avec frais à payer",
        categorie="autre",
        poids=25,
        motifs=(
            r"\b(offre|poste|emploi|job|khdma|khedma|travail)\b.{0,120}\b(frais|payer|paiement|caution|depot|versement)\b",
            r"\b(frais|paiement|versement)\b.{0,80}\b(visa|billet d'avion|billet|dossier de candidature|formation obligatoire)\b",
        ),
        explication="Un emploi est proposé avec des frais à payer (inscription, visa, dossier). Un véritable employeur ne fait jamais payer le candidat pour l'embaucher.",
    ),
    Regle(
        nom="Emploi à l'étranger",
        categorie="autre",
        poids=10,
        motifs=(
            r"\b(emploi|travail|job|poste|khdma|khedma|offre)\b.{0,50}\b(etranger|canada|europe|dubai|qatar|italie|espagne|allemagne|turquie|arabie|koweit)\b",
            r"\bkhdma\b|\bkhedma\b|\bdubai\b",
        ),
        explication="Une offre d'emploi à l'étranger est proposée : c'est un terrain fréquent des arnaques. Vérifiez l'employeur et le processus de recrutement auprès des autorités compétentes.",
    ),
    Regle(
        nom="Fausse détresse d'un proche",
        categorie="autre",
        poids=15,
        motifs=(
            r"\b(j'ai|j ai) besoin (urgent |vraiment |tres )?d'?argent\b",
            r"\baidez?[- ]moi\b.{0,40}\b(urgence|argent|virement|somme)\b",
            r"\b(envoyez|envoie|vire|virez)[- ]moi\b.{0,30}\b(argent|somme|dh|mad|euros?|dollars?)\b",
        ),
        explication="Un proche, ou une personne qui se présente comme tel, demande de l'argent en urgence. Appelez la personne sur son numéro habituel avant tout envoi.",
    ),
)


def normaliser_texte(texte: str) -> str:
    """Met le texte en minuscules, sans accents ni harakat, avec des espaces normalisés, pour la comparaison."""
    texte = _retirer_accents(texte).translate(_CORRESPONDANCES_ARABES).lower()
    texte = texte.replace("’", "'")
    return re.sub(r"\s+", " ", texte).strip()


def _retirer_accents(texte: str) -> str:
    """Retire les accents latins et les marques diacritiques arabes via la décomposition Unicode."""
    decompose = unicodedata.normalize("NFKD", texte)
    return "".join(caractere for caractere in decompose if not unicodedata.combining(caractere))


def _normaliser_motif(motif: str) -> str:
    """Applique aux motifs regex la même normalisation que celle du texte analysé."""
    return _retirer_accents(motif).translate(_CORRESPONDANCES_ARABES).replace("’", "'")


def _compiler(motifs: tuple) -> tuple:
    """Compile une liste de motifs après normalisation, insensible à la casse."""
    return tuple(re.compile(_normaliser_motif(motif), re.IGNORECASE) for motif in motifs)


def _extraire_mots(motifs: tuple, texte: str) -> list[str]:
    """Renvoie jusqu'à trois extraits du texte correspondant aux motifs d'une règle."""
    trouves: list[str] = []
    for motif in motifs:
        for correspondance in motif.finditer(texte):
            extrait = correspondance.group(0).strip()
            if len(extrait) > 60:
                extrait = extrait[:57] + "…"
            if extrait and extrait not in trouves:
                trouves.append(extrait)
            if len(trouves) >= MAX_MOTS:
                return trouves
    return trouves


def analyser_regles(texte: str) -> dict:
    """Applique toutes les règles au texte et renvoie le score, les signaux déclenchés et les scores par catégorie."""
    texte_normalise = normaliser_texte(texte or "")
    signaux = []
    for regle, motifs, contexte in _REGLES_COMPILEES:
        mots = _extraire_mots(motifs, texte_normalise)
        if not mots:
            continue
        if contexte and not any(motif.search(texte_normalise) for motif in contexte):
            continue
        signaux.append(
            {
                "libelle": regle.nom,
                "categorie": regle.categorie,
                "poids": regle.poids,
                "explication": regle.explication,
                "mots": mots,
            }
        )
    brut = sum(signal["poids"] for signal in signaux)
    scores_categories = {
        code: min(100, sum(signal["poids"] for signal in signaux if signal["categorie"] == code))
        for code in CATEGORIES
    }
    return {
        "score": min(100, brut),
        "brut": brut,
        "signaux": signaux,
        "scores_categories": scores_categories,
    }


_CORRESPONDANCES_ARABES = str.maketrans({"أ": "ا", "إ": "ا", "آ": "ا", "ـ": ""})
_REGLES_COMPILEES = tuple((regle, _compiler(regle.motifs), _compiler(regle.contexte)) for regle in REGLES)
