# THE canonical cross-source fingerprint. Single implementation — every
# consumer (snapshot, validator, merge) calls these, never re-derives.
def squeeze: gsub("\\s+"; " ") | sub("^ "; "") | sub(" $"; "");
def norm_loc:
  ascii_downcase
  | gsub("[^a-z0-9 ]"; " ")
  | gsub("\\b(area|region|greater|metropolitan)\\b"; " ")
  | squeeze;
def fp($c; $t; $l):
  ($c | ascii_downcase | squeeze) + "|" + ($t | ascii_downcase | squeeze) + "|" + ($l | norm_loc);
