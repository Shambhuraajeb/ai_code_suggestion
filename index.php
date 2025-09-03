<?php
    $username = $_POST['username'];
    $password = $_POST['password'];
    $sql = "SELECT * FROM users WHERE username = '$username' AND password = '$password'";

    echo "<h1>Welcome, " . $_GET['name'] . "!</h1>";

