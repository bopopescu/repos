<?php

if ($_POST['_submit_check']) 
{
	$username="root";
	$password="";
	$database="retreat";
	$link=mysqli_connect(localhost,$username,$password,$database);
	if(!$link){ echo " mysql connection not working";}
	$name=$_POST['name'];
	echo  "<script  type='text/javascript'>
           alert('$name : Your abstract has been submited. Thank you');
          </script>"; 
	$email=$_POST['email'];
	$pi=$_POST['pi'];
	$tshirt=$_POST['tshirt'];
	$roommate1=$_POST['roommate1'];
	$roommate2=$_POST['roommate2'];
	$roommate3=$_POST['roommate3'];
	$roommate4=$_POST['roommate4'];
	$query=" insert INTO register (name,email,pi,tshirt,roommate1,roommate2,roommate3,roommate4) VALUES('$name','$email','$pi','$tshirt','$roommate1','$roommate2','$roommate3','$roommate4')";  
	$result=mysqli_query($link,$query);
	if(!result){ echo "error in query";}
	$strLocation = "./retreat.html";
	header("location:".$strLocation);
	mysql_close(); 
}
?>

<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
<meta http-equiv="Content-Type" content="text/html; charset=iso-8859-1" />
<title>MCB Retreat</title>
<style type="text/css">
<!--
.style3 {
	font-family: "Monotype Corsiva";
	color: #FF0000;
}
.style7 {
	color: #000000;
	font-family: "Times New Roman", Times, serif;
	font-weight: bold;
}
.style8 {
	font-size: 16px;
	font-family: "Lucida Sans Unicode";
	font-weight: bold;
}
-->
</style>
</head>

<body>
<form method="post" name="abstract" action="<?php echo $_SERVER['PHP_SELF'];?>">
<table width="800" height="747" border="0" align="center" cellpadding="0" cellspacing="0">
  <tr>
    <td height="747" align="center" valign="top" background="scroll_back.jpg"><table width="800" height="535" border="0" align="center" cellpadding="0" cellspacing="0">
      <tr>
        <td width="161" height="96">&nbsp;</td>
        <td width="117">&nbsp;</td>
        <td width="93">&nbsp;</td>
        <td width="343">&nbsp;</td>
        <td width="86">&nbsp;</td>
      </tr>
      <tr>
        <td height="39" colspan="5" align="center" valign="middle"><h1><span class="style3">MCB Retreat 2006</span> </h1></td>
        </tr>
      
      <tr>
        <td height="30" colspan="5" align="center" valign="middle"><p class="style8">Registration</p></td>
        </tr>
      <tr>
        <td height="34">&nbsp;</td>
        <td colspan="2" align="left"><strong>Name:</strong></td>
        <td align="left"> <input type="text" name="name" /></td>
        <td>&nbsp;</td>
      </tr>
      <tr>
        <td height="32">&nbsp;</td>
        <td colspan="2" align="left"><strong>E-mail:</strong></td>
        <td align="left"><input type="text" name="email" /></td>
        <td>&nbsp;</td>
      </tr>
      <tr>
        <td height="32">&nbsp;</td>
        <td colspan="2" align="left"><strong>PI's Name: </strong></td>
        <td align="left"><input type="text" name="pi" /></td>
        <td>&nbsp;</td>
      </tr>
      <tr>
        <td height="46" colspan="5" align="center"><div class="style7" style="margin:10px 40px 10px 60px">Free T-Shirts will be given out at the registration table for those attending</div></td>
        </tr>
     
	  <tr>
        <td height="33">&nbsp;</td>
        <td colspan="2" align="left"><strong>T-Shirt Size: </strong></td>
        <td align="left"><select name="tshirt"  >
          <option>XS</option>
          <option>S</option>
          <option>M</option>
          <option>L</option>
          <option>XL</option>
        </select></td>
        <td>&nbsp;</td>
      </tr>
      <tr>
        <td height="46" colspan="5" align="center" class="style7"><div class="style7" style="margin:10px 40px 10px 50px">
          <div align="left">Submit up to 4 names of people you would like to room with.&nbsp;&nbsp;All rooms willbe same-sex, and will be organized according to your preferences below.Note that most rooms hold 3 people, so not all groups of 5 will be  accommodated.</div>
        </div></td>
        </tr>
      <tr>
        <td height="33">&nbsp;</td>
        <td colspan="2" align="left"><strong>Roommate Choices: </strong></td>
        <td align="left"> <input type="text" name="roommate1" /></td>
        <td>&nbsp;</td>
      </tr>
      <tr>
        <td height="29">&nbsp;</td>
        <td colspan="2" align="left" valign="middle">&nbsp;</td>
        <td align="left"><input type="text" name="roommate2" /></td>
        <td>&nbsp;</td>
      </tr>
      <tr>
        <td height="29">&nbsp;</td>
        <td colspan="2" align="left" valign="middle">&nbsp;</td>
        <td align="left"><input type="text" name="roommate3" /></td>
        <td>&nbsp;</td>
      </tr>
      <tr>
        <td height="29">&nbsp;</td>
        <td colspan="2" align="left" valign="middle">&nbsp;</td>
        <td align="left"><input type="text" name="roommate4" /></td>
        <td>&nbsp;</td>
      </tr>
      <tr>
        <td height="27" colspan="5" align="center" valign="middle"><input type="hidden" name="_submit_check" value="1"/><input type="submit" name="submit" ></td>
        </tr>
    </table></td>
  </tr>
</table>
</form>
</body>
</html>


