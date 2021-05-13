# Project 1

Web Programming with Python and


Crea un usuario en register para poder utilizar la aplicación. Una vez registrado
loguéate y busca un libro.

La búsqueda la puedes hacer por ISBN, titulo o autor, aunque puede que solo escribas un
caracter para que busque todos los posibles resultados.

Realizada la búsqueda ingresa al link del ISBN en color azul para mostrar información del
libro, esa información la he extraido de la API, y utilizo http://covers.openlibrary.org/b/isbn/
para generar la carátula del libro que estamso buscando.

En la parte de abajo podremos agregar comentarios, esos cometarios se agregarán a una base
de datos, según el isbn del libro y el user_id de quien lo publicó, para que se pueda identificar
quién hizo ese comentario y con redirect una vez que se suba el comentario, que aparezca de forma
inmediata.

Cabe resaltar que la API utilizada con contiene todos los libros importados a la base de datos,
por lo que no te procupes si ves un error de servidor, ya que si ese libro no lo contiene la API,
no podrá extraer la información que le hemos solicitado, pero mientras tanto, todo funcionará correcto.

Este fue mi primer proyecto de Flask.