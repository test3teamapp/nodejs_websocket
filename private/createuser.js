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
      callback({ success: true });
    }
  });
}

main().catch((err) => console.log(err));

async function main() {
  console.log("Creating user");
  await mongoose.connect("mongodb://localhost:27017/webchatroom");

  createANewUser("cang", "olatalefta", function (error, success) {
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
