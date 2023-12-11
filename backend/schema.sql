DROP TABLE IF EXISTS user;
DROP TABLE IF EXISTS crawler;
DROP TABLE IF EXISTS IG_Clone_Account;

CREATE TABLE user (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  username TEXT UNIQUE NOT NULL,
  password TEXT NOT NULL
);

CREATE TABLE crawler (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL,
  username TEXT NOT NULL,
  full_name TEXT NOT NULL,
  phone TEXT NOT NULL,
  email TEXT NOT NULL,
  FOREIGN KEY (user_id) REFERENCES user (id)
);

INSERT INTO crawler (id, user_id, username, full_name, email, phone) VALUES (1, 1, "macymeinv","Macy Liu","macy@flex-star.com","");
INSERT INTO crawler (id, user_id, username, full_name, email, phone) VALUES (2, 1, "catpetlovers001","Kitty","catpetlovers001@gmail.com","");
INSERT INTO crawler (id, user_id, username, full_name, email, phone) VALUES (3, 1, "amelartpalette","Amelia","amelia@frameandflame.com","");
INSERT INTO crawler (id, user_id, username, full_name, email, phone) VALUES (4, 1, "studio_apartment_natasha","","","0998204381");
INSERT INTO crawler (id, user_id, username, full_name, email, phone) VALUES (5, 1, "kuhteeuh","Kuhteeuh","Todd@hastatimusicnetwork.com","");
INSERT INTO crawler (id, user_id, username, full_name, email, phone) VALUES (6, 1, "hightechhoops","Joel Kyle","hightechhoops@gmail.com","");
INSERT INTO crawler (id, user_id, username, full_name, email, phone) VALUES (7, 1, "whispers.cats","whisper,s cats","","0572878168");
INSERT INTO crawler (id, user_id, username, full_name, email, phone) VALUES (8, 1, "tattooboutiquelarissa","Larissa Mathijs - Fineline tattoo art.","tattooboutiquelarissa@hotmail.com","");

CREATE TABLE IG_Clone_Account (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  username TEXT NOT NULL,
  password TEXT NOT NULL,
  user_id INTEGER NOT NULL,
  FOREIGN KEY (user_id) REFERENCES user (id)
);

INSERT INTO IG_Clone_Account (id, username, password, user_id) VALUES (1,"tieuvietquyen","gflluRx3KV8t",1);
INSERT INTO IG_Clone_Account (id, username, password, user_id) VALUES (2,"phamhongquy9354","y0ym1my8yj6j",1);
INSERT INTO IG_Clone_Account (id, username, password, user_id) VALUES (3,"phamhienthuc1200","b8bf2fe7ee8e",1);