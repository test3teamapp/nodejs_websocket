const bcrypt = require("bcryptjs");
const mongoose = require("mongoose");

const UserModel = require("../models/user.js");

const saltRounds = 10;

function createANewUser(username, password, callback) {
  const newUserDbDocument = new UserModel({
    username: username,
    password: password,
  });

  newUserDbDocument.save(function (error) {
    if (error) {
      callback({ error: true });
    } else {
      callback({ error: false });
    }
  });
}

main().catch((err) => console.log(err));

async function main() {
  const uname = "cang";
  const pass = "Olatalefta2U";

  console.log("Creating user " + uname );
  await mongoose.connect("mongodb://localhost:27017/webchatroom");

  // if user exists ...

  UserModel.find.byName(uname).exec((err, users) => {
    if (err){
        console.log("Error while searching for users: " + err );
    }else {
        console.log("I found existing users by that name: " + users);
    }

  });

  createANewUser(uname, pass, function (error) {
    if (error) {
      console.log("failed");
    } else {
      console.log("done");
    }
  });
}

if (require.main === module) {
  main();
}
