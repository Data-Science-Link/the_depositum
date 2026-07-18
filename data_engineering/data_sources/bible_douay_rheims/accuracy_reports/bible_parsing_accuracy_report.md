# Bible Validation Report

- Generated (UTC): `2026-04-19T23:12:07.024395+00:00`
- Overall status: `PASS`

## Integrity Summary

Plain-English: this section reports the core structural and parser-health checks for the Bible output.
- `files_found`: whether all 73 expected Bible book files exist.
- `verses_checked`: total verses compared against parsed source `c:v.` paragraphs.
- `skipped_commentary` / `skipped_preface`: non-scripture blocks detected and excluded.
- `joined_continuations`: wrapped verse lines merged back into one verse.

- files_found: `73`
- verses_checked: `35734`
- skipped_commentary: `1845`
- skipped_preface: `1551`
- joined_continuations: `11`

## Trend / Warnings

Plain-English: this checks run-to-run drift in parser behavior (especially skipped block counts).
If this says `None`, no drift crossed the configured alert threshold, and no external spot-check fetch warnings were raised.

- None

## Integrity Errors

Plain-English: this is where hard validation failures appear.
Checks include: expected filenames, chapter counts, monotonic verse numbering, duplicate detection, verse-number set equality vs source, and normalized verse-text equality vs source.
If this says `None`, all those checks passed on this run.

- None

## DRBO Spot Check

Plain-English: this samples random verse references and compares normalized local output to DRBO for external confidence.
Before comparison, canonical variant mappings are applied to BOTH sides to reduce false negatives from spelling variants.
- Canonical variant mappings in use:
  - `to morrow` -> `tomorrow`
  - `bloodofferings` -> `blood offerings`
  - `mayst` -> `mayest`
  - `fulfil` -> `fulfill`
  - `fahter` -> `father`
  - `begot` -> `beget`
- `exact_matched`: normalized texts are exactly equal after mapping.
- `near_matched`: normalized texts are not exact but are above the near-match similarity threshold.
- `mismatched`: same reference found in both, but remains below the near-match threshold.
- `unavailable`: DRBO text for that sampled reference could not be retrieved/parsing-ready.
If `unavailable` is `0`, none of the attempted references failed DRBO retrieval/parsing.

- Sample size: `100` | exact: `91` (91.0%) | near: `7` | exact+near: `98` (98.0%) | mismatched: `2` | unavailable: `0` | attempted_refs: `100` | seed: `1776640327` | near-threshold: `0.985`
- Replacement sampling is enabled: if a sampled ref is unavailable, we keep sampling additional refs until target sample size is reached or candidates are exhausted.

| Book | Ref | Result | Similarity | Local norm | DRBO norm |
| --- | --- | --- | --- | --- | --- |
| Joshua | 19:7 | text mismatch | 0.9677 | and remmon and athor and asan four cities and their villages | ain and remmon and athor and asan four cities and their villages |
| 1 Corinthians | 10:8 | text mismatch | 0.9801 | neither let us commit fornication as some of them that committed fornication and there fell in one day three and twenty thousand | neither let us commit fornication as some of them committed fornication and there fell in one day three and twenty thousand |
| Psalms | 4:1 | near_match | 0.9877 | unto the end in verses a psalm for david | unto the end in verses a psalm for david |
| Judges | 5:30 | near_match | 0.9908 | perhaps he is now dividing the spoils and the fairest of the women is chosen out for him garments of divers colours are given to sisara for his prey and furniture of different kinds is heaped together to adorn necks | perhaps he is now dividing the spoils and the fairest of the women is chosen out for him garments of divers colours are given to sisara for his prey and furniture of different kinds is heaped together to adorn the necks |
| 1 John | 2:20 | near_match | 0.9920 | but you have the unction from the holy one and know all things | but you have the unction from the holy one and know all things |
| Joshua | 8:9 | near_match | 0.9920 | and he sent them away and they went on to the place of the ambush and abode between bethel and hai on the west side of the city of hai but josue staid that night in the midst of the people | and he sent them away and they went on to the place of the ambush and abode between bethel and hai on the west side of the city of hai but josue stayed that night in the midst of the people |
| Psalms | 21:19 | near_match | 0.9930 | they lparted my garments amongst them and upon my vesture they cast lots | they parted my garments amongst them and upon my vesture they cast lots |
| Nehemiah | 10:35 | near_match | 0.9965 | and that we would bring the firstfruits of our land and the firstfruits of all fruit of every tree from year to year in the house of our lord | and that we would bring the first fruits of our land and the firstfruits of all fruit of every tree from year to year in the house of our lord |
| Amos | 7:16 | near_match | 0.9967 | and now hear thou the word of the lord thou sayest thou shalt not prophesy against israel and thou shalt not drop thy word upon the house of the idol | and now hear thou the word of the lord thou sayest thou shalt not prophesy against israel and thou shalt not drop thy word upon the house of the idol |
| 1 Chronicles | 1:9 | exact_match | 1.0000 | and the sons of chus saba and hevila sabatha and regma and sabathaca and the sons of regma saba and dadan | and the sons of chus saba and hevila sabatha and regma and sabathaca and the sons of regma saba and dadan |
| 1 Chronicles | 2:25 | exact_match | 1.0000 | and the sons of jerameel the firstborn of hesron were ram his firstborn and buna and aram and asom and achia | and the sons of jerameel the firstborn of hesron were ram his firstborn and buna and aram and asom and achia |
| 1 Kings | 2:29 | exact_match | 1.0000 | and it was told king solomon that joab was fled into the tabernacle of the lord and was by the altar and solomon sent banaias the son of joiada saying go kill him | and it was told king solomon that joab was fled into the tabernacle of the lord and was by the altar and solomon sent banaias the son of joiada saying go kill him |
| 1 Kings | 11:3 | exact_match | 1.0000 | and he had seven hundred wives as queens and three hundred concubines and the women turned away his heart | and he had seven hundred wives as queens and three hundred concubines and the women turned away his heart |
| 1 Maccabees | 9:3 | exact_match | 1.0000 | in the first month of the hundred and fiftysecond year they brought the army to jerusalem | in the first month of the hundred and fiftysecond year they brought the army to jerusalem |
| 1 Maccabees | 16:6 | exact_match | 1.0000 | and he and his people pitched their camp over against them and he saw that the people were afraid to go over the river so he went over first then the men seeing him passed over after him | and he and his people pitched their camp over against them and he saw that the people were afraid to go over the river so he went over first then the men seeing him passed over after him |
| 1 Samuel | 12:6 | exact_match | 1.0000 | and samuel said to the people it is the lord who made moses and aaron and brought our fathers out of the land of egypt | and samuel said to the people it is the lord who made moses and aaron and brought our fathers out of the land of egypt |
| 1 Samuel | 13:23 | exact_match | 1.0000 | and the army of the philistines went out in order to advance further in machmas | and the army of the philistines went out in order to advance further in machmas |
| 1 Samuel | 17:24 | exact_match | 1.0000 | and all the israelites when they saw the man fled from his face fearing him exceedingly | and all the israelites when they saw the man fled from his face fearing him exceedingly |
| 2 Chronicles | 6:35 | exact_match | 1.0000 | then hear thou from heaven their prayers and their supplications and revenge them | then hear thou from heaven their prayers and their supplications and revenge them |
| 2 Corinthians | 6:2 | exact_match | 1.0000 | for he saith in an accepted time have i heard thee and in the day of salvation have i helped thee behold now is the acceptable time behold now is the day of salvation | for he saith in an accepted time have i heard thee and in the day of salvation have i helped thee behold now is the acceptable time behold now is the day of salvation |
| 2 Corinthians | 7:11 | exact_match | 1.0000 | for behold this selfsame thing that you were made sorrowful according to god how great carefulness it worketh in you yea defence yea indignation yea fear yea desire yea zeal yea revenge in all things you have shewed yourselves to be undefiled in the matter | for behold this selfsame thing that you were made sorrowful according to god how great carefulness it worketh in you yea defence yea indignation yea fear yea desire yea zeal yea revenge in all things you have shewed yourselves to be undefiled in the matter |
| 2 Corinthians | 12:9 | exact_match | 1.0000 | and he said to me my grace is sufficient for thee for power is made perfect in infirmity gladly therefore will i glory in my infirmities that the power of christ may dwell in me | and he said to me my grace is sufficient for thee for power is made perfect in infirmity gladly therefore will i glory in my infirmities that the power of christ may dwell in me |
| 2 Kings | 13:22 | exact_match | 1.0000 | now hazael king of syria afflicted israel all the days of joachaz | now hazael king of syria afflicted israel all the days of joachaz |
| 2 Kings | 18:1 | exact_match | 1.0000 | in the third year of osee the son of ela king of israel reigned ezechias the son of achaz king of juda | in the third year of osee the son of ela king of israel reigned ezechias the son of achaz king of juda |
| 2 Maccabees | 4:6 | exact_match | 1.0000 | for he saw that except the king took care it was impossible that matters should be settled in peace or that simon would cease from his folly | for he saw that except the king took care it was impossible that matters should be settled in peace or that simon would cease from his folly |
| 2 Peter | 2:8 | exact_match | 1.0000 | for in sight and hearing he was just dwelling among them who from day to day vexed the just soul with unjust works | for in sight and hearing he was just dwelling among them who from day to day vexed the just soul with unjust works |
| 2 Samuel | 9:5 | exact_match | 1.0000 | then king david sent and brought him out of the house of machir the son of ammiel of lodabar | then king david sent and brought him out of the house of machir the son of ammiel of lodabar |
| Acts | 1:11 | exact_match | 1.0000 | who also said ye men of galilee why stand you looking up to heaven this jesus who is taken up from you into heaven shall so come as you have seen him going into heaven | who also said ye men of galilee why stand you looking up to heaven this jesus who is taken up from you into heaven shall so come as you have seen him going into heaven |
| Acts | 2:6 | exact_match | 1.0000 | and when this was noised abroad the multitude came together and were confounded in mind because that every man heard them speak in his own tongue | and when this was noised abroad the multitude came together and were confounded in mind because that every man heard them speak in his own tongue |
| Acts | 7:20 | exact_match | 1.0000 | at the same time was moses born and he was acceptable to god who was nourished three months in his fathers house | at the same time was moses born and he was acceptable to god who was nourished three months in his fathers house |
| Acts | 16:6 | exact_match | 1.0000 | and when they had passed through phrygia and the country of galatia they were forbidden by the holy ghost to preach the word in asia | and when they had passed through phrygia and the country of galatia they were forbidden by the holy ghost to preach the word in asia |
| Baruch | 2:1 | exact_match | 1.0000 | wherefore the lord our god hath made good his word that he spoke to us and to our judges that have judged israel and to our kings and to our princes and to all israel and juda | wherefore the lord our god hath made good his word that he spoke to us and to our judges that have judged israel and to our kings and to our princes and to all israel and juda |
| Baruch | 3:6 | exact_match | 1.0000 | for thou art the lord our god and we will praise thee o lord | for thou art the lord our god and we will praise thee o lord |
| Daniel | 14:3 | exact_match | 1.0000 | the king also worshipped him and went every day to adore him but daniel adored his god and the king said to him why dost thou not adore bel | the king also worshipped him and went every day to adore him but daniel adored his god and the king said to him why dost thou not adore bel |
| Deuteronomy | 28:11 | exact_match | 1.0000 | the lord will make thee abound with all goods with the fruit of thy womb and the fruit of thy cattle with the fruit of thy land which the lord swore to thy fathers that he would give thee | the lord will make thee abound with all goods with the fruit of thy womb and the fruit of thy cattle with the fruit of thy land which the lord swore to thy fathers that he would give thee |
| Esther | 11:12 | exact_match | 1.0000 | and when mardochai had seen this and arose out of his bed he was thinking what god would do and he kept it fixed in his mind desirous to know what the dream should signify | and when mardochai had seen this and arose out of his bed he was thinking what god would do and he kept it fixed in his mind desirous to know what the dream should signify |
| Exodus | 4:7 | exact_match | 1.0000 | and he said put back thy hand into thy bosom he put it back and brought it out again and it was like the other flesh | and he said put back thy hand into thy bosom he put it back and brought it out again and it was like the other flesh |
| Exodus | 8:8 | exact_match | 1.0000 | but pharao called moses and aaron and said to them pray ye to the lord to take away the frogs from me and from my people and i will let the people go to sacrifice to the lord | but pharao called moses and aaron and said to them pray ye to the lord to take away the frogs from me and from my people and i will let the people go to sacrifice to the lord |
| Exodus | 16:22 | exact_match | 1.0000 | but on the sixth day they gathered twice as much that is two gomors every man and all the rulers of the multitude came and told moses | but on the sixth day they gathered twice as much that is two gomors every man and all the rulers of the multitude came and told moses |
| Exodus | 17:16 | exact_match | 1.0000 | because the hand of the throne of the lord and the war of the lord shall be against amalec from generation to generation | because the hand of the throne of the lord and the war of the lord shall be against amalec from generation to generation |
| Exodus | 28:24 | exact_match | 1.0000 | and the golden chains thou shalt join to the rings that are in the ends thereof | and the golden chains thou shalt join to the rings that are in the ends thereof |
| Ezekiel | 1:14 | exact_match | 1.0000 | and the living creatures ran and returned like flashes of lightning | and the living creatures ran and returned like flashes of lightning |
| Ezekiel | 12:2 | exact_match | 1.0000 | son of man thou dwellest in the midst of a provoking house who have eyes to see and see not and ears to hear and hear not for they are a provoking house | son of man thou dwellest in the midst of a provoking house who have eyes to see and see not and ears to hear and hear not for they are a provoking house |
| Ezekiel | 12:8 | exact_match | 1.0000 | and the word of the lord came to me in the morning saying | and the word of the lord came to me in the morning saying |
| Ezekiel | 32:23 | exact_match | 1.0000 | whose graves are set in the lowest parts of the pit and his multitude lay round about his grave all of them slain and fallen by the sword they that heretofore spread terror in the land of the living | whose graves are set in the lowest parts of the pit and his multitude lay round about his grave all of them slain and fallen by the sword they that heretofore spread terror in the land of the living |
| Ezekiel | 38:12 | exact_match | 1.0000 | to take spoils and lay hold on the prey to lay thy hand upon them that had been wasted and afterwards restored and upon the people that is gathered together out of the nations which hath begun to possess and to dwell in the midst of the earth | to take spoils and lay hold on the prey to lay thy hand upon them that had been wasted and afterwards restored and upon the people that is gathered together out of the nations which hath begun to possess and to dwell in the midst of the earth |
| Genesis | 20:2 | exact_match | 1.0000 | and he said of sara his wife she is my sister so abimelech the king of gerara sent and took her | and he said of sara his wife she is my sister so abimelech the king of gerara sent and took her |
| Genesis | 43:33 | exact_match | 1.0000 | they sat before him the firstborn according to his birthright and the youngest according to his age and they wondered very much | they sat before him the firstborn according to his birthright and the youngest according to his age and they wondered very much |
| Hosea | 7:15 | exact_match | 1.0000 | and i have chastised them and strengthened their arms and they have imagined evil against me | and i have chastised them and strengthened their arms and they have imagined evil against me |
| Isaiah | 41:12 | exact_match | 1.0000 | thou shalt seek them and shalt not find the men that resist thee they shall be as nothing and as a thing consumed the men that war against thee | thou shalt seek them and shalt not find the men that resist thee they shall be as nothing and as a thing consumed the men that war against thee |
| Isaiah | 44:19 | exact_match | 1.0000 | they do not consider in their mind nor know nor have the thought to say i have burnt part of it in the fire and i have baked bread upon the coals thereof i have broiled flesh and have eaten and of the residue thereof shall i make an idol shall i fall down before the stock of a tree | they do not consider in their mind nor know nor have the thought to say i have burnt part of it in the fire and i have baked bread upon the coals thereof i have broiled flesh and have eaten and of the residue thereof shall i make an idol shall i fall down before the stock of a tree |
| Isaiah | 45:13 | exact_match | 1.0000 | i have raised him up to justice and i will direct all his ways he shall build my city and let go my captives not for ransom nor for presents saith the lord the god of hosts | i have raised him up to justice and i will direct all his ways he shall build my city and let go my captives not for ransom nor for presents saith the lord the god of hosts |
| Isaiah | 63:18 | exact_match | 1.0000 | they have possessed thy holy people as nothing our enemies have trodden down thy sanctuary | they have possessed thy holy people as nothing our enemies have trodden down thy sanctuary |
| James | 1:19 | exact_match | 1.0000 | you know my dearest brethren and let every man be swift to hear but slow to speak and slow to anger | you know my dearest brethren and let every man be swift to hear but slow to speak and slow to anger |
| James | 2:9 | exact_match | 1.0000 | but if you have respect to persons you commit sin being reproved by the law as transgressors | but if you have respect to persons you commit sin being reproved by the law as transgressors |
| Job | 15:31 | exact_match | 1.0000 | he shall not believe being vainly deceived by error that he may be redeemed with any price | he shall not believe being vainly deceived by error that he may be redeemed with any price |
| Job | 29:15 | exact_match | 1.0000 | i was an eye to the blind and a foot to the lame | i was an eye to the blind and a foot to the lame |
| Job | 32:1 | exact_match | 1.0000 | so these three men ceased to answer job because he seemed just to himself | so these three men ceased to answer job because he seemed just to himself |
| John | 4:22 | exact_match | 1.0000 | you adore that which you know not we adore that which we know for salvation is of the jews | you adore that which you know not we adore that which we know for salvation is of the jews |
| Leviticus | 3:12 | exact_match | 1.0000 | if his offering be a goat and he offer it to the lord | if his offering be a goat and he offer it to the lord |
| Leviticus | 10:13 | exact_match | 1.0000 | and you shall eat it in a holy place which is given to thee and thy sons of the oblations of the lord as it hath been commanded me | and you shall eat it in a holy place which is given to thee and thy sons of the oblations of the lord as it hath been commanded me |
| Leviticus | 16:29 | exact_match | 1.0000 | and this shall be to you an everlasting ordinance the seventh month the tenth day of the month you shall afflict your souls and shall do no work whether it be one of your own country or a stranger that sojourneth among you | and this shall be to you an everlasting ordinance the seventh month the tenth day of the month you shall afflict your souls and shall do no work whether it be one of your own country or a stranger that sojourneth among you |
| Leviticus | 17:11 | exact_match | 1.0000 | because the life of the flesh is in the blood and i have given it to you that you may make atonement with it upon the altar for your souls and the blood may be for an expiation of the soul | because the life of the flesh is in the blood and i have given it to you that you may make atonement with it upon the altar for your souls and the blood may be for an expiation of the soul |
| Leviticus | 25:16 | exact_match | 1.0000 | the more years remain after the jubilee the more shall the price increase and the less time is counted so much the less shall the purchase cost for he shall sell to thee the time of the fruits | the more years remain after the jubilee the more shall the price increase and the less time is counted so much the less shall the purchase cost for he shall sell to thee the time of the fruits |
| Leviticus | 25:48 | exact_match | 1.0000 | after the sale he may be redeemed he that will of his brethren shall redeem him | after the sale he may be redeemed he that will of his brethren shall redeem him |
| Leviticus | 25:53 | exact_match | 1.0000 | his wages being allowed for which he served before he shall not afflict him violently in thy sight | his wages being allowed for which he served before he shall not afflict him violently in thy sight |
| Luke | 9:61 | exact_match | 1.0000 | and another said i will follow thee lord but let me first take my leave of them that are at my house | and another said i will follow thee lord but let me first take my leave of them that are at my house |
| Luke | 16:17 | exact_match | 1.0000 | and it is easier for heaven and earth to pass than one tittle of the law to fall | and it is easier for heaven and earth to pass than one tittle of the law to fall |
| Luke | 24:51 | exact_match | 1.0000 | and it came to pass whilst he blessed them he departed from them and was carried up to heaven | and it came to pass whilst he blessed them he departed from them and was carried up to heaven |
| Malachi | 2:10 | exact_match | 1.0000 | have we not all one father hath not one god created us why then doth every one of us despise his brother violating the covenant of our fathers | have we not all one father hath not one god created us why then doth every one of us despise his brother violating the covenant of our fathers |
| Mark | 13:30 | exact_match | 1.0000 | amen i say to you that this generation shall not pass until all these things be done | amen i say to you that this generation shall not pass until all these things be done |
| Matthew | 14:11 | exact_match | 1.0000 | and his head was brought in a dish and it was given to the damsel and she brought it to her mother | and his head was brought in a dish and it was given to the damsel and she brought it to her mother |
| Matthew | 22:45 | exact_match | 1.0000 | if david then call him lord how is he his son | if david then call him lord how is he his son |
| Matthew | 25:30 | exact_match | 1.0000 | and the unprofitable servant cast ye out into the exterior darkness there shall be weeping and gnashing of teeth | and the unprofitable servant cast ye out into the exterior darkness there shall be weeping and gnashing of teeth |
| Matthew | 26:70 | exact_match | 1.0000 | but he denied before them all saying i know not what thou sayest | but he denied before them all saying i know not what thou sayest |
| Numbers | 18:13 | exact_match | 1.0000 | all the firstripe of the fruits that the ground bringeth forth and which are brought to the lord shall be for thy use he that is clean in thy house shall eat them | all the firstripe of the fruits that the ground bringeth forth and which are brought to the lord shall be for thy use he that is clean in thy house shall eat them |
| Philippians | 1:17 | exact_match | 1.0000 | and some out of contention preach christ not sincerely supposing that they raise affliction to my bands | and some out of contention preach christ not sincerely supposing that they raise affliction to my bands |
| Proverbs | 7:7 | exact_match | 1.0000 | and i see little ones i behold a foolish young man | and i see little ones i behold a foolish young man |
| Psalms | 89:15 | exact_match | 1.0000 | we have rejoiced for the days in which thou hast humbled us for the years in which we have seen evils | we have rejoiced for the days in which thou hast humbled us for the years in which we have seen evils |
| Psalms | 96:10 | exact_match | 1.0000 | you that love the lord hate evil the lord preserveth the souls of his saints he will deliver them out of the hand of the sinner | you that love the lord hate evil the lord preserveth the souls of his saints he will deliver them out of the hand of the sinner |
| Psalms | 105:41 | exact_match | 1.0000 | and he delivered them into the hands of the nations and they that hated them had dominion over them | and he delivered them into the hands of the nations and they that hated them had dominion over them |
| Psalms | 106:43 | exact_match | 1.0000 | who is wise and will keep these things and will understand the mercies of the lord | who is wise and will keep these things and will understand the mercies of the lord |
| Psalms | 113:21 | exact_match | 1.0000 | he hath blessed all that fear the lord both little and great | he hath blessed all that fear the lord both little and great |
| Psalms | 118:82 | exact_match | 1.0000 | my eyes have failed for thy word saying when wilt thou comfort me | my eyes have failed for thy word saying when wilt thou comfort me |
| Psalms | 125:4 | exact_match | 1.0000 | turn again our captivity o lord as a stream in the south | turn again our captivity o lord as a stream in the south |
| Psalms | 145:3 | exact_match | 1.0000 | in the children of men in whom there is no salvation | in the children of men in whom there is no salvation |
| Revelation | 12:15 | exact_match | 1.0000 | and the serpent cast out of his mouth after the woman water as it were a river that he might cause her to be carried away by the river | and the serpent cast out of his mouth after the woman water as it were a river that he might cause her to be carried away by the river |
| Revelation | 13:8 | exact_match | 1.0000 | and all that dwell upon the earth adored him whose names are not written in the book of life of the lamb which was slain from the beginning of the world | and all that dwell upon the earth adored him whose names are not written in the book of life of the lamb which was slain from the beginning of the world |
| Sirach | 11:23 | exact_match | 1.0000 | for it is easy in the eyes of god on a sudden to make the poor man rich | for it is easy in the eyes of god on a sudden to make the poor man rich |
| Sirach | 14:9 | exact_match | 1.0000 | the eye of the covetous man is insatiable in his portion of iniquity he will not be satisfied till he consume his own soul drying it up | the eye of the covetous man is insatiable in his portion of iniquity he will not be satisfied till he consume his own soul drying it up |
| Sirach | 18:3 | exact_match | 1.0000 | for who shall search out his glorious acts | for who shall search out his glorious acts |
| Sirach | 21:16 | exact_match | 1.0000 | the knowledge of a wise man shall abound like a flood and his counsel continueth like a fountain of life | the knowledge of a wise man shall abound like a flood and his counsel continueth like a fountain of life |
| Sirach | 28:13 | exact_match | 1.0000 | a hasty contention kindleth a fire and a hasty quarrel sheddeth blood and a tongue that beareth witness bringeth death | a hasty contention kindleth a fire and a hasty quarrel sheddeth blood and a tongue that beareth witness bringeth death |
| Sirach | 33:10 | exact_match | 1.0000 | some of them god made high and great days and some of them he put in the number of ordinary days and all men are from the ground and out of the earth from whence adam was created | some of them god made high and great days and some of them he put in the number of ordinary days and all men are from the ground and out of the earth from whence adam was created |
| Sirach | 35:6 | exact_match | 1.0000 | thou shalt not appear empty in the sight of the lord | thou shalt not appear empty in the sight of the lord |
| Sirach | 47:26 | exact_match | 1.0000 | and solomon had an end with his fathers | and solomon had an end with his fathers |
| Titus | 3:9 | exact_match | 1.0000 | but avoid foolish questions and genealogies and contentions and strivings about the law for they are unprofitable and vain | but avoid foolish questions and genealogies and contentions and strivings about the law for they are unprofitable and vain |
| Tobit | 4:10 | exact_match | 1.0000 | for thus thou storest up to thyself a good reward for the day of necessity | for thus thou storest up to thyself a good reward for the day of necessity |
| Zephaniah | 1:3 | exact_match | 1.0000 | i will gather man and beast i will gather the birds of the air and the fishes of the sea and the ungodly shall meet with ruin and i will destroy men from off the face of the land saith the lord | i will gather man and beast i will gather the birds of the air and the fishes of the sea and the ungodly shall meet with ruin and i will destroy men from off the face of the land saith the lord |
| Zephaniah | 3:7 | exact_match | 1.0000 | i said surely thou wilt fear me thou wilt receive correction and her dwelling shall not perish for all things wherein i have visited her but they rose early and corrupted all their thoughts | i said surely thou wilt fear me thou wilt receive correction and her dwelling shall not perish for all things wherein i have visited her but they rose early and corrupted all their thoughts |

## DRBO Mismatch Hunt (extended sampling)

Plain-English: after the fixed random sample above, we run a second pass with the same comparison rules. It keeps drawing new random verses until it records **20** strict **text mismatch** outcomes (similarity strictly below the near-match threshold—not counting near matches), **or** until **400** successful comparisons are accumulated—whichever occurs first. Summary bullets below include full-run exact/near/mismatch counts; the markdown table lists **only** problematic (**text mismatch**) rows (same columns as the random sample table).
- Independent shuffle seed offset from the random sample seed: `1000003` (mismatch-hunt seed = random-sample seed + offset).

- Stop rule: stop after `20` **text mismatch** results (strict; not near match) or after `400` successful comparisons—whichever happens first. Observed text mismatches in this table: `9`. Stopped because: `max_samples`.
- Sample size: `400` | exact: `366` (91.5%) | near: `25` | exact+near: `391` (97.75%) | mismatched: `9` | unavailable: `0` | attempted_refs: `400` | seed: `1777640330` | near-threshold: `0.985`
- Replacement sampling is enabled: if a sampled ref is unavailable, we keep sampling additional refs until the stop rule is satisfied or candidates are exhausted.

- **Table:** only **text mismatch** rows (strict; below near-match threshold). Exact and near matches are omitted here but remain in the aggregate counts above.

| Book | Ref | Result | Similarity | Local norm | DRBO norm |
| --- | --- | --- | --- | --- | --- |
| Joshua | 6:27 | text mismatch | 0.3546 | and the lord was with josue and his name was noised throughout all the land | and the lord was with josue and his name was noised throughout all the land 26 cursed jericho in the mystical sense signifies iniquity the sounding of the trumpets by the priests the preaching of the word of god by which the walls of jericho are thrown down when sinners are converted and a dreadful curse will light on them who build them up again |
| 1 Samuel | 17:49 | text mismatch | 0.7259 | and he put his hand into his scrip and took a stone and cast it with the sling and fetching it about struck the philistine in the forehead and he fell on his face upon the earth | and he put his hand into his scrip and took a stone and cast it with the sling and fetching it about struck the philistine in the forehead and the stone was fixed in his forehead and he fell on his face upon the earth |
| 1 Kings | 18:26 | text mismatch | 0.8649 | and they took the bullock which he gave them and dressed it and they called on the name of baal from morning even until noon saying o baal hear us but there was no voice nor any that answered and they leaped over the altar that they had made | and they took the bullock which he gave them and dressed it and they called on the name of baal from morning even till noon saying o baal hear us but there was no voice nor any that answered and they leaped over the altar that they had made |
| Psalms | 128:1 | text mismatch | 0.8742 | a gradual canticle often have they fought against me from my youth let israel now say | often have they fought against me from my youth let israel now say |
| 1 Kings | 7:20 | text mismatch | 0.8921 | and again there were other chapiters on the top of the pillars above according to the measure of the pillar over against the network and of pomegranates there were two hundred in rows round about the other chapiter | and again other chapiters in the top of the pillars above according to the measure of the pillar over against the network and of pomegranates there were two hundred in rows round about the other chapiter |
| 1 Samuel | 17:56 | text mismatch | 0.9455 | and the king said inquire thou whose son this young man is | and the king said inquire thou whose son this man is |
| Sirach | 20:2 | text mismatch | 0.9697 | the lust of an eunuch shall deflour a young maiden | the lust of an eunuch shall devour a young maiden |
| Leviticus | 9:18 | text mismatch | 0.9804 | he immolated also the bullock and the ram and peace offerings of the people and his sons brought him the blood which he poured upon the altar round about | he immolated also the bullock and the ram the peace offerings of the people and his sons brought him the blood which he poured upon the altar round about |
| 1 Kings | 19:12 | text mismatch | 0.9815 | and after the earthquake a fire but the lord is not in the fire and after the fire a whistling of a gentle air | and after the earthquake a fire the lord is not in the fire and after the fire a whistling of a gentle air |
