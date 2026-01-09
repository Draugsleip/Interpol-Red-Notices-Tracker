function openModal(src){
    const modal = document.getElementById('imageModal');
    const modalImg = document.getElementById('img');

    if (modal && modalImg){
        modal.style.display = "flex";
        modalImg.src = src;
    }
}
function closeModal(){

    const modal = document.getElementById('imageModal');
    if(modal){
        modal.style.display = "none";
    }
}

window.onclick = function(event){
    const modal = this.document.getElementById("imageModal");
    if(event.target == modal){
        closeModal();
    }
}

