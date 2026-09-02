# THE canonical cross-source fingerprint. Single implementation — every
# consumer (snapshot, validator, merge) calls these, never re-derives.
def squeeze: gsub("\\s+"; " ") | sub("^ "; "") | sub(" $"; "");
def fold_diacritics:
  gsub("[äÄàÀáÁâÂãÃ]"; "a") | gsub("[ëËèÈéÉêÊ]"; "e") | gsub("[ïÏìÌíÍîÎ]"; "i")
  | gsub("[öÖòÒóÓôÔõÕøØ]"; "o") | gsub("[üÜùÙúÚûÛ]"; "u") | gsub("[çÇ]"; "c")
  | gsub("[ñÑ]"; "n") | gsub("ß"; "ss") | gsub("[æÆ]"; "ae") | gsub("[åÅ]"; "a");
def norm_loc:
  ascii_downcase
  | fold_diacritics
  | gsub("[^a-z0-9 ]"; " ")
  | gsub("\\b(area|region|greater|metropolitan)\\b"; " ")
  | squeeze;
# A literal "|" inside any component would break the three-field form the
# validator enforces (company|title|location), so it is folded to a space first.
def strip_pipe: gsub("\\|"; " ");
def fp($c; $t; $l):
  ($c | strip_pipe | ascii_downcase | fold_diacritics | squeeze) + "|" + ($t | strip_pipe | ascii_downcase | fold_diacritics | squeeze) + "|" + ($l | strip_pipe | norm_loc);
