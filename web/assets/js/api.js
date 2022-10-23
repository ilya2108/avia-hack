var csv=document.getElementById('inputFile').files[0];
var formData=new FormData();
formData.append("uploadCsv",csv);
var request = new XMLHttpRequest();


document.addEventListener("click", function (event) {
  if (!event.target.matches("#send")) return;

     request.setRequestHeader("Content-type", "multipart/form-data");
     request.open("POST","https://0.0.0.0:5000/api/tasks/send", true);
     request.onreadystatechange = function (){
        if(request.readyState === XMLHttpRequest.DONE && request.status === 200) {
        console.log("yey");
        }
    }

    request.send(formData);
    
});
