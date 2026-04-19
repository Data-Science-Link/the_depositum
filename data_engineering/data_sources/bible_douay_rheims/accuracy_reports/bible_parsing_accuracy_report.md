# Bible Validation Report

- Generated (UTC): `2026-04-19T22:50:07.935639+00:00`
- Overall status: `PASS`

## Integrity Summary

Plain-English: this section reports the core structural and parser-health checks for the Bible output.
- `files_found`: whether all 73 expected Bible book files exist.
- `verses_checked`: total verses compared against parsed source `c:v.` paragraphs.
- `skipped_commentary` / `skipped_preface`: non-scripture blocks detected and excluded.
- `joined_continuations`: wrapped verse lines merged back into one verse.

- files_found: `73`
- verses_checked: `35735`
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

- Sample size: `100` | exact: `90` (90.0%) | near: `7` | exact+near: `97` (97.0%) | mismatched: `3` | unavailable: `0` | attempted_refs: `100` | seed: `1776639007` | near-threshold: `0.985`
- Replacement sampling is enabled: if a sampled ref is unavailable, we keep sampling additional refs until target sample size is reached or candidates are exhausted.

| Book | Ref | Result | Similarity | Local norm | DRBO norm |
| --- | --- | --- | --- | --- | --- |
| Proverbs | 12:23 | text mismatch | 0.2930 | lying lips are an abomination to the lord but they that deal faithfully please him | a cautious man concealeth knowledge and the heart of fools publisheth folly |
| 2 Kings | 11:9 | text mismatch | 0.6462 | and the centurions did according to all things that joiada the priest had commanded them and takiug every one their men that went in on the sabbath with them that went out in the sabbath came to joiada the priest | and the centurions did according to all things that joiada the priest had commanded them and taking every one their men that went in on the sabbath with them that went out on the sabbath came to joiada the priest |
| Job | 5:22 | text mismatch | 0.9796 | in destruction and famine thou shalt laugh and thou shalt not be afraid of the beasts of the earth | in destruction and famine then shalt laugh and thou shalt not be afraid of the beasts of the earth |
| Isaiah | 9:4 | near_match | 0.9926 | for the yoke of their burden and the rod of their shoulder and the sceptre of their oppressor thou hast overcome as in the day of madian | for the yoke of their burden and the rod of their shoulder and the sceptre of their oppressor thou hast overcome as in the day of median |
| Numbers | 24:7 | near_match | 0.9930 | water shall flow out of his bucket and his seed shall be in many waters for agag his king shall be removed and his kingdom shall be taken away | water shall flow out of his bucket and his seed shall be in many waters for agag his king shall be removed and his kingdom shall be taken awry |
| Jonah | 2:4 | near_match | 0.9931 | and thou hast cast me forth into the deep in the heart of the sea and a flood hast compassed me all thy billows and thy waves have passed over me | and thou hast cast me forth into the deep in the heart of the sea and a flood hath compassed me all thy billows and thy waves have passed over me |
| Judges | 4:2 | near_match | 0.9944 | and the lord delivered them up into the hands of jabin king of chanaan who reigned in asor and he had a general of his army named sisara and he dwelt in haroseth of the gentiles | and the lord delivered them up into the hands of jaban king of chanaan who reigned in asor and he had a general of his army named sisara and he dwelt in haroseth of the gentiles |
| Jeremiah | 7:14 | near_match | 0.9967 | i will do to this house in which my name is called upon and in which you trust and to the place which i have given you and your fathers as i did to silo | i will do to this house in which my name is called upon and in which you trust and to the places which i have given you and your fathers as i did to silo |
| 1 Maccabees | 8:30 | near_match | 0.9975 | and if after this one party or the other shall have a mind to add to these articles or take away any thing they may do it at their pleasure and whatsoever they shall add or take away shall be ratified | and if after this one party or the other shall have a mind to add to these articles or take away anything they may do it at their pleasure and whatsoever they shall add or take away shall be ratified |
| Judges | 7:20 | near_match | 0.9981 | and when they sounded their trurmpets in three places round about the camp and had broken their pitchers they held their lamps in their left hands and with their right hands the trumpets which they blew and they cried out the sword of the lord and of gedeon | and when they sounded their trumpets in three places round about the camp and had broken their pitchers they held their lamps in their left hands and with their right hands the trumpets which they blew and they cried out the sword of the lord and of gedeon |
| 1 Kings | 2:30 | exact_match | 1.0000 | and banaias came to the tabernacle of the lord and said to him thus saith the king come forth and he said i will not come forth but here i will die banaias brought word back to the king saying thus saith joab and thus he answered me | and banaias came to the tabernacle of the lord and said to him thus saith the king come forth and he said i will not come forth but here i will die banaias brought word back to the king saying thus saith joab and thus he answered me |
| 1 Kings | 21:8 | exact_match | 1.0000 | so she wrote letters in achabs name and sealed them with his ring and sent them to the ancients and the chief men that were in his city and that dwelt with naboth | so she wrote letters in achabs name and sealed them with his ring and sent them to the ancients and the chief men that were in his city and that dwelt with naboth |
| 1 Maccabees | 6:56 | exact_match | 1.0000 | was returned from persia and media with the army that went with him and that he sought to take upon him the affairs of the kingdom | was returned from persia and media with the army that went with him and that he sought to take upon him the affairs of the kingdom |
| 1 Samuel | 28:3 | exact_match | 1.0000 | now samuel was dead and all israel mourned for him and buried him in ramatha his city and saul had put away all the magicians and soothsayers out of the land | now samuel was dead and all israel mourned for him and buried him in ramatha his city and saul had put away all the magicians and soothsayers out of the land |
| 1 Thessalonians | 2:6 | exact_match | 1.0000 | nor sought we glory of men neither of you nor of others | nor sought we glory of men neither of you nor of others |
| 2 Chronicles | 6:41 | exact_match | 1.0000 | now therefore arise o lord god into thy resting place thou and the ark of thy strength let thy priests o lord god put on salvation and thy saints rejoice in good things | now therefore arise o lord god into thy resting place thou and the ark of thy strength let thy priests o lord god put on salvation and thy saints rejoice in good things |
| 2 Chronicles | 7:2 | exact_match | 1.0000 | neither could the priests enter into the temple of the lord because the majesty of the lord had filled the temple of the lord | neither could the priests enter into the temple of the lord because the majesty of the lord had filled the temple of the lord |
| 2 Chronicles | 11:5 | exact_match | 1.0000 | and roboam dwelt in jerusalem and built walled cities in juda | and roboam dwelt in jerusalem and built walled cities in juda |
| 2 Chronicles | 15:18 | exact_match | 1.0000 | and the things which his father had vowed and he himself had vowed he brought into the house of the lord gold and silver and vessels of divers uses | and the things which his father had vowed and he himself had vowed he brought into the house of the lord gold and silver and vessels of divers uses |
| 2 Chronicles | 18:8 | exact_match | 1.0000 | and the king of israel called one of the eunuchs and said to him call quickly micheas the son of jemla | and the king of israel called one of the eunuchs and said to him call quickly micheas the son of jemla |
| 2 Chronicles | 24:22 | exact_match | 1.0000 | and king joas did not remember the kindness that joiada his father had done to him but killed his son and when he died he said the lord see and require it | and king joas did not remember the kindness that joiada his father had done to him but killed his son and when he died he said the lord see and require it |
| 2 Samuel | 13:36 | exact_match | 1.0000 | and when he made an end of speaking the kings sons also appeared and coming in they lifted up their voice and wept and the king also and all his servants wept very much | and when he made an end of speaking the kings sons also appeared and coming in they lifted up their voice and wept and the king also and all his servants wept very much |
| 2 Samuel | 14:10 | exact_match | 1.0000 | and the king said if any one shall say ought against thee bring him to me and he shall not touch thee any more | and the king said if any one shall say ought against thee bring him to me and he shall not touch thee any more |
| Acts | 7:27 | exact_match | 1.0000 | but he that did the injury to his neighbour thrust him away saying who hath appointed thee prince and judge over us | but he that did the injury to his neighbour thrust him away saying who hath appointed thee prince and judge over us |
| Acts | 11:16 | exact_match | 1.0000 | and i remembered the word of the lord how that he said john indeed baptized with water but you shall be baptized with the holy ghost | and i remembered the word of the lord how that he said john indeed baptized with water but you shall be baptized with the holy ghost |
| Acts | 12:1 | exact_match | 1.0000 | and at the same time herod the king stretched forth his hands to afflict some of the church | and at the same time herod the king stretched forth his hands to afflict some of the church |
| Acts | 18:9 | exact_match | 1.0000 | and the lord said to paul in the night by a vision do not fear but speak and hold not thy peace | and the lord said to paul in the night by a vision do not fear but speak and hold not thy peace |
| Baruch | 6:14 | exact_match | 1.0000 | and this hath in his hand a sword or an axe but cannot save himself from war or from robbers whereby be it known to you that they are not gods | and this hath in his hand a sword or an axe but cannot save himself from war or from robbers whereby be it known to you that they are not gods |
| Daniel | 2:1 | exact_match | 1.0000 | in the second year of the reign of nabuchodonosor nabuchodonosor had a dream and his spirit was terrified and his dream went out of his mind | in the second year of the reign of nabuchodonosor nabuchodonosor had a dream and his spirit was terrified and his dream went out of his mind |
| Daniel | 10:11 | exact_match | 1.0000 | and he said to me daniel thou man of desires understand the words that i speak to thee and stand upright for i am sent now to thee and when he had said this word to me i stood trembling | and he said to me daniel thou man of desires understand the words that i speak to thee and stand upright for i am sent now to thee and when he had said this word to me i stood trembling |
| Deuteronomy | 7:7 | exact_match | 1.0000 | not because you surpass all nations in number is the lord joined unto you and hath chosen you for you are the fewest of any people | not because you surpass all nations in number is the lord joined unto you and hath chosen you for you are the fewest of any people |
| Deuteronomy | 14:5 | exact_match | 1.0000 | the hart and the roe the buffle the chamois the pygarg the wild goat the camelopardalus | the hart and the roe the buffle the chamois the pygarg the wild goat the camelopardalus |
| Deuteronomy | 14:15 | exact_match | 1.0000 | and the ostrich and the owl and the larus and the hawk according to its kind | and the ostrich and the owl and the larus and the hawk according to its kind |
| Deuteronomy | 24:14 | exact_match | 1.0000 | thou shalt not refuse the hire of the needy and the poor whether he be thy brother or a stranger that dwelleth with thee in the land and is within thy gates | thou shalt not refuse the hire of the needy and the poor whether he be thy brother or a stranger that dwelleth with thee in the land and is within thy gates |
| Ephesians | 4:30 | exact_match | 1.0000 | and grieve not the holy spirit of god whereby you are sealed unto the day of redemption | and grieve not the holy spirit of god whereby you are sealed unto the day of redemption |
| Esther | 15:10 | exact_match | 1.0000 | and when he had lifted up his countenance and with burning eyes had shewn the wrath of his heart the queen sunk down and her colour turned pale and she rested her weary head upon her handmaid | and when he had lifted up his countenance and with burning eyes had shewn the wrath of his heart the queen sunk down and her colour turned pale and she rested her weary head upon her handmaid |
| Esther | 16:24 | exact_match | 1.0000 | and let every province and city that will not be partaker of this solemnity perish by the sword and by fire and be destroyed in such manner as to be made unpassable both to men and beasts for an example of contempt and disobedience | and let every province and city that will not be partaker of this solemnity perish by the sword and by fire and be destroyed in such manner as to be made unpassable both to men and beasts for an example of contempt and disobedience |
| Exodus | 5:4 | exact_match | 1.0000 | the king of egypt said to them why do you moses and aaron draw off the people from their works get you gone to your burdens | the king of egypt said to them why do you moses and aaron draw off the people from their works get you gone to your burdens |
| Exodus | 30:11 | exact_match | 1.0000 | and the lord spoke to moses saying | and the lord spoke to moses saying |
| Exodus | 31:7 | exact_match | 1.0000 | the tabernacle of the covenant and the ark of the testimony and the propitiatory that is over it and all the vessels of the tabernacle | the tabernacle of the covenant and the ark of the testimony and the propitiatory that is over it and all the vessels of the tabernacle |
| Ezekiel | 17:4 | exact_match | 1.0000 | he cropped off the top of the twigs thereof and carried it away into the land of chanaan and he set it in a city of merchants | he cropped off the top of the twigs thereof and carried it away into the land of chanaan and he set it in a city of merchants |
| Ezekiel | 34:13 | exact_match | 1.0000 | and i will bring them out from the peoples and will gather them out of the countries and will bring them to their own land and i will feed them in the mountains of israel by the rivers and in all the habitations of the land | and i will bring them out from the peoples and will gather them out of the countries and will bring them to their own land and i will feed them in the mountains of israel by the rivers and in all the habitations of the land |
| Ezra | 4:21 | exact_match | 1.0000 | now therefore hear the sentence hinder those men that this city be not built till further orders be given by me | now therefore hear the sentence hinder those men that this city be not built till further orders be given by me |
| Galatians | 5:17 | exact_match | 1.0000 | for the flesh lusteth against the spirit and the spirit against the flesh for these are contrary one to another so that you do not the things that you would | for the flesh lusteth against the spirit and the spirit against the flesh for these are contrary one to another so that you do not the things that you would |
| Genesis | 3:8 | exact_match | 1.0000 | and when they heard the voice of the lord god walking in paradise at the afternoon air adam and his wife hid themselves from the face of the lord god amidst the trees of paradise | and when they heard the voice of the lord god walking in paradise at the afternoon air adam and his wife hid themselves from the face of the lord god amidst the trees of paradise |
| Genesis | 5:9 | exact_match | 1.0000 | and enos lived ninety years and beget cainan | and enos lived ninety years and beget cainan |
| Genesis | 5:20 | exact_match | 1.0000 | and all the days of jared were nine hundred and sixtytwo years and he died | and all the days of jared were nine hundred and sixtytwo years and he died |
| Genesis | 6:6 | exact_match | 1.0000 | it repented him that he had made man on the earth and being touched inwardly with sorrow of heart | it repented him that he had made man on the earth and being touched inwardly with sorrow of heart |
| Genesis | 18:8 | exact_match | 1.0000 | he took also butter and milk and the calf which he had boiled and set before them but he stood by them under the tree | he took also butter and milk and the calf which he had boiled and set before them but he stood by them under the tree |
| Genesis | 21:32 | exact_match | 1.0000 | and they made a league for the well of oath | and they made a league for the well of oath |
| Genesis | 28:15 | exact_match | 1.0000 | and i will be thy keeper whithersoever thou goest and will bring thee back into this land neither will i leave thee till i shall have accomplished all that i have said | and i will be thy keeper whithersoever thou goest and will bring thee back into this land neither will i leave thee till i shall have accomplished all that i have said |
| Genesis | 41:12 | exact_match | 1.0000 | there was there a young man a hebrew servant to the same captain of the soldiers to whom we told our dreams | there was there a young man a hebrew servant to the same captain of the soldiers to whom we told our dreams |
| Hosea | 4:5 | exact_match | 1.0000 | and thou shalt fall today and the prophet also shall fall with thee in the night i have made thy mother to be silent | and thou shalt fall today and the prophet also shall fall with thee in the night i have made thy mother to be silent |
| Isaiah | 3:17 | exact_match | 1.0000 | the lord will make bald the crown of the head of the daughters of sion and the lord will discover their hair | the lord will make bald the crown of the head of the daughters of sion and the lord will discover their hair |
| Isaiah | 29:16 | exact_match | 1.0000 | this thought of yours is perverse as if the clay should think against the potter and the work should say to the maker thereof thou madest me not or the thing framed should say to him that fashioned it thou understandest not | this thought of yours is perverse as if the clay should think against the potter and the work should say to the maker thereof thou madest me not or the thing framed should say to him that fashioned it thou understandest not |
| Isaiah | 46:4 | exact_match | 1.0000 | even to your old age i am the same and to your grey hairs i will carry you i have made you and i will bear i will carry and will save | even to your old age i am the same and to your grey hairs i will carry you i have made you and i will bear i will carry and will save |
| Isaiah | 48:21 | exact_match | 1.0000 | they thirsted not in the desert when he led them out he brought forth water out of the rock for them and he clove the rock and the waters gushed out | they thirsted not in the desert when he led them out he brought forth water out of the rock for them and he clove the rock and the waters gushed out |
| James | 2:3 | exact_match | 1.0000 | and you have respect to him that is clothed with the fine apparel and shall say to him sit thou here well but say to the poor man stand thou there or sit under my footstool | and you have respect to him that is clothed with the fine apparel and shall say to him sit thou here well but say to the poor man stand thou there or sit under my footstool |
| Jeremiah | 6:27 | exact_match | 1.0000 | i have set thee for a strong trier among my people and thou shalt know and prove their way | i have set thee for a strong trier among my people and thou shalt know and prove their way |
| Jeremiah | 49:30 | exact_match | 1.0000 | flee ye get away speedily sit in deep holes you that inhabit asor saith the lord for nabuchodonosor king of babylon hath taken counsel against you and hath conceived designs against you | flee ye get away speedily sit in deep holes you that inhabit asor saith the lord for nabuchodonosor king of babylon hath taken counsel against you and hath conceived designs against you |
| Jeremiah | 52:25 | exact_match | 1.0000 | he also took out of the city one eunuch that was chief over the men of war and seven men of them that were near the kings person that were found in the city and a scribe an officer of the army who exercised the young soldiers and threescore men of the people of the land that were found in the midst of the city | he also took out of the city one eunuch that was chief over the men of war and seven men of them that were near the kings person that were found in the city and a scribe an officer of the army who exercised the young soldiers and threescore men of the people of the land that were found in the midst of the city |
| Job | 5:7 | exact_match | 1.0000 | man is born to labour and the bird to fly | man is born to labour and the bird to fly |
| Job | 18:3 | exact_match | 1.0000 | why are we reputed as beasts and counted vile before you | why are we reputed as beasts and counted vile before you |
| Job | 41:5 | exact_match | 1.0000 | who can open the doors of his face his teeth are terrible round about | who can open the doors of his face his teeth are terrible round about |
| John | 14:12 | exact_match | 1.0000 | otherwise believe for the very works sake amen amen i say to you he that believeth in me the works that i do he also shall do and greater than these shall he do | otherwise believe for the very works sake amen amen i say to you he that believeth in me the works that i do he also shall do and greater than these shall he do |
| John | 18:40 | exact_match | 1.0000 | then cried they all again saying not this man but barabbas now barabbas was a robber | then cried they all again saying not this man but barabbas now barabbas was a robber |
| Joshua | 15:21 | exact_match | 1.0000 | and the cities from the uttermost parts of the children of juda by the borders of edom to the south were cabseel and eder and jagur | and the cities from the uttermost parts of the children of juda by the borders of edom to the south were cabseel and eder and jagur |
| Judges | 2:13 | exact_match | 1.0000 | forsaking him and serving baal and astaroth | forsaking him and serving baal and astaroth |
| Lamentations | 3:43 | exact_match | 1.0000 | samech thou hast covered in thy wrath and hast struck us thou hast killed and hast not spared | samech thou hast covered in thy wrath and hast struck us thou hast killed and hast not spared |
| Leviticus | 7:11 | exact_match | 1.0000 | this is the law of the sacrifice of peace offerings that is offered to the lord | this is the law of the sacrifice of peace offerings that is offered to the lord |
| Leviticus | 23:1 | exact_match | 1.0000 | and the lord spoke to moses saying | and the lord spoke to moses saying |
| Leviticus | 24:18 | exact_match | 1.0000 | he that killeth a beast shall make it good that is to say shall give beast for beast | he that killeth a beast shall make it good that is to say shall give beast for beast |
| Luke | 5:20 | exact_match | 1.0000 | whose faith when he saw he said man thy sins are forgiven thee | whose faith when he saw he said man thy sins are forgiven thee |
| Luke | 19:29 | exact_match | 1.0000 | and it came to pass when he was come nigh to bethphage and bethania unto the mount called olivet he sent two of his disciples | and it came to pass when he was come nigh to bethphage and bethania unto the mount called olivet he sent two of his disciples |
| Mark | 10:10 | exact_match | 1.0000 | and in the house again his disciples asked him concerning the same thing | and in the house again his disciples asked him concerning the same thing |
| Matthew | 6:7 | exact_match | 1.0000 | and when you are praying speak not much as the heathens for they think that in their much speaking they may be heard | and when you are praying speak not much as the heathens for they think that in their much speaking they may be heard |
| Matthew | 16:10 | exact_match | 1.0000 | nor the seven loaves among four thousand men and how many baskets you took up | nor the seven loaves among four thousand men and how many baskets you took up |
| Nehemiah | 4:4 | exact_match | 1.0000 | hear thou our god for we are despised turn their reproach upon their own head and give them to be despised in a land of captivity | hear thou our god for we are despised turn their reproach upon their own head and give them to be despised in a land of captivity |
| Numbers | 11:21 | exact_match | 1.0000 | and moses said there are six hundred thousand footmen of this people and sayest thou i will give them flesh to eat a whole month | and moses said there are six hundred thousand footmen of this people and sayest thou i will give them flesh to eat a whole month |
| Numbers | 16:25 | exact_match | 1.0000 | and moses arose and went to dathan and abiron and the ancients of israel following him | and moses arose and went to dathan and abiron and the ancients of israel following him |
| Numbers | 17:1 | exact_match | 1.0000 | and the lord spoke to moses saying | and the lord spoke to moses saying |
| Numbers | 28:9 | exact_match | 1.0000 | and on the sabbath day you shall offer two lambs of a year old without blemish and two tenths of flour tempered with oil in sacrifice and the libations | and on the sabbath day you shall offer two lambs of a year old without blemish and two tenths of flour tempered with oil in sacrifice and the libations |
| Proverbs | 10:10 | exact_match | 1.0000 | he that winketh with the eye shall cause sorrow and the foolish in lips shall be beaten | he that winketh with the eye shall cause sorrow and the foolish in lips shall be beaten |
| Psalms | 4:10 | exact_match | 1.0000 | for thou o lord singularly hast settled me in hope | for thou o lord singularly hast settled me in hope |
| Psalms | 13:1 | exact_match | 1.0000 | unto the end a psalm for david the fool hath said in his heart there is no god they are corrupt and are become abominable in their ways there is none that doth good no not one | unto the end a psalm for david the fool hath said in his heart there is no god they are corrupt and are become abominable in their ways there is none that doth good no not one |
| Psalms | 19:5 | exact_match | 1.0000 | may he give thee according to thy own heart and confirm all thy counsels | may he give thee according to thy own heart and confirm all thy counsels |
| Psalms | 21:32 | exact_match | 1.0000 | there shall be declared to the lord a generation to come and the heavens shall shew forth his justice to a people that shall be born which the lord hath made | there shall be declared to the lord a generation to come and the heavens shall shew forth his justice to a people that shall be born which the lord hath made |
| Psalms | 34:22 | exact_match | 1.0000 | thou hast seen o lord be not thou silent o lord depart not from me | thou hast seen o lord be not thou silent o lord depart not from me |
| Psalms | 35:1 | exact_match | 1.0000 | unto the end for the servant of god david himself | unto the end for the servant of god david himself |
| Psalms | 36:17 | exact_match | 1.0000 | for the arms of the wicked shall be broken in pieces but the lord strengtheneth the just | for the arms of the wicked shall be broken in pieces but the lord strengtheneth the just |
| Psalms | 39:2 | exact_match | 1.0000 | with expectation i have waited for the lord and he was attentive to me | with expectation i have waited for the lord and he was attentive to me |
| Psalms | 118:26 | exact_match | 1.0000 | i have declared my ways and thou hast heard me teach me thy justifications | i have declared my ways and thou hast heard me teach me thy justifications |
| Psalms | 118:77 | exact_match | 1.0000 | let thy tender mercies come unto me and i shall live for thy law is my meditation | let thy tender mercies come unto me and i shall live for thy law is my meditation |
| Revelation | 17:9 | exact_match | 1.0000 | and here is the understanding that hath wisdom the seven heads are seven mountains upon which the woman sitteth and they are seven kings | and here is the understanding that hath wisdom the seven heads are seven mountains upon which the woman sitteth and they are seven kings |
| Romans | 15:32 | exact_match | 1.0000 | that i may come to you with joy by the will of god and may be refreshed with you | that i may come to you with joy by the will of god and may be refreshed with you |
| Sirach | 31:4 | exact_match | 1.0000 | the poor man hath laboured in his low way of life and in the end he is still poor | the poor man hath laboured in his low way of life and in the end he is still poor |
| Sirach | 34:3 | exact_match | 1.0000 | the vision of dreams is the resemblance of one thing to another as when a mans likeness is before the face of a man | the vision of dreams is the resemblance of one thing to another as when a mans likeness is before the face of a man |
| Sirach | 41:21 | exact_match | 1.0000 | be ashamed of fornication before father and mother and of a lie before a governor and a man in power | be ashamed of fornication before father and mother and of a lie before a governor and a man in power |
| Tobit | 1:11 | exact_match | 1.0000 | and when by the captivity he with his wife and his son and all his tribe was come to the city of ninive | and when by the captivity he with his wife and his son and all his tribe was come to the city of ninive |
| Wisdom | 14:12 | exact_match | 1.0000 | for the beginning of fornication is the devising of idols and the invention of them is the corruption of life | for the beginning of fornication is the devising of idols and the invention of them is the corruption of life |

## DRBO Mismatch Hunt (extended sampling)

Plain-English: after the fixed random sample above, we run a second pass with the same comparison rules. It keeps drawing new random verses until it records **20** strict **text mismatch** outcomes (similarity strictly below the near-match threshold—not counting near matches), **or** until **400** successful comparisons are accumulated—whichever occurs first. Summary bullets below include full-run exact/near/mismatch counts; the markdown table lists **only** problematic (**text mismatch**) rows (same columns as the random sample table).
- Independent shuffle seed offset from the random sample seed: `1000003` (mismatch-hunt seed = random-sample seed + offset).

- Stop rule: stop after `20` **text mismatch** results (strict; not near match) or after `400` successful comparisons—whichever happens first. Observed text mismatches in this table: `7`. Stopped because: `max_samples`.
- Sample size: `400` | exact: `380` (95.0%) | near: `13` | exact+near: `393` (98.25%) | mismatched: `7` | unavailable: `0` | attempted_refs: `400` | seed: `1777639010` | near-threshold: `0.985`
- Replacement sampling is enabled: if a sampled ref is unavailable, we keep sampling additional refs until the stop rule is satisfied or candidates are exhausted.

- **Table:** only **text mismatch** rows (strict; below near-match threshold). Exact and near matches are omitted here but remain in the aggregate counts above.

| Book | Ref | Result | Similarity | Local norm | DRBO norm |
| --- | --- | --- | --- | --- | --- |
| James | 5:20 | text mismatch | 0.4196 | he must know that he who causeth a sinner to be converted from the error of his way shall save his soul from death and shall cover a multitude of sins | he must know that he who causeth a sinner to be converted from the error of his way shall save his soul from death and shall cover a multitude of sins 16 confess therefore your sins one to another that is to the priests of the church whom ver 14 he had ordered to be called for and brought in to the sick moreover to confess to persons who had no power to forgive sins would be useless hence the precept here means that we must confess to men whom god hath appointed and who by their ordination and jurisdiction have received the power of remitting sins in his name |
| Psalms | 121:1 | text mismatch | 0.8984 | a gradual canticle i rejoiced at the things that were said to me we shall go into the house of the lord | i rejoiced at the things that were said to me we shall go into the house of the lord |
| Genesis | 41:53 | text mismatch | 0.9429 | now when the seven years of plenty that had been in egypt were passed | now when the seven years of the plenty that had been in egypt were past |
| Jeremiah | 8:20 | text mismatch | 0.9672 | the harvest is past the summer is ended and we are not saved | the harvest is passed the summer is ended and we are not saved |
| Exodus | 34:25 | text mismatch | 0.9707 | thou shalt not offer the blood of my sacrifice upon leaven neither shall there remain in the morning any thing of the victim of the solemnity of the phase | thou shalt not offer the blood of my sacrifice upon leaven neither shall there remain in the morning any thing of the victim of the solemnity of the lord |
| 1 Samuel | 17:41 | text mismatch | 0.9718 | and the philistine came on and drew nigh against david and his armourbearer went before him | and the philistine came on and drew nigh against david and his armourbearer before him |
| Numbers | 3:17 | text mismatch | 0.9730 | and there were found sons of levi by their names gerson and caath merari | and there were found sons of levi by their names gerson and caath and merari |
