#
#  this file is used to compress a list of js file
#  
#  jianjun  1.4 2012
#
#  backup the original file , and replace it with the compressed file
#

cmd=""
COMPRESS_CMD_GOOGLE="java -jar compiler.jar --compilation_level ADVANCED_OPTIMIZATIONS --js inputfile --js_output_file outputfile"
COMPRESS_CMD_YUI="java -jar yuicompressor-2.4.7.jar inputfile -o outputfile"
COMPRESS_CMD=$COMPRESS_CMD_YUI
BACKUPTAILER=".back"

#check command
case $1 in
    "--restore" | "--compress" | "-r" | "-c")
	cmd=$1
	shift 1
	;;
    *)
	#default do compress file
	cmd="--compress" 
	;;
esac

function file_restore()
{
    filename=$1
    echo "$filename"
    if [ ! -s $filename$BACKUPTAILER ];then
	echo "$filename$BACKUPTAILER not exist or size is zero!"
	return
    fi
    cp $filename$BACKUPTAILER $filename
}

function file_checkout()
{
    filename=$1
    echo "$filename"
    rm $filename
    git checkout $filename
}

function file_compress()
{
    filename=$1
    echo "file :" $filename
    if [ ! -s $filename ];then
	echo "$filename not exist or size is zero!"
	return
    fi
    # 1 back the file
    cp $filename $filename$BACKUPTAILER
    echo "Back $filename -> $filename$BACKUPTAILER"
    # 2 compress the file
    sed_filename=$(echo $filename | sed 's/\//\\\//')
    echo $filename
    _CMD=$(echo $COMPRESS_CMD | sed "s/inputfile/$sed_filename/" |sed "s/outputfile/$sed_filename.tmp/")
    echo "Compressing $filename"
    #echo $_CMD
    $_CMD
    mv $filename.tmp $filename
    echo -e "\n\n"
}

#file_op cmd file_name
function file_op()
{
    case $1 in
	"--restore"|"-r")
	    file_restore $2
	    ;;
	"--checkout"|"-c")
	    file_checkout $2
	    ;;
	*)
	    file_compress $2
	    ;;
    esac
}

#check input filelist , if have , do filelist operation
if [ $# != 0 ];then
    echo "== use input file instend"
    file_list=$*

    for file in $file_list;do
	file_op $cmd $file
    done
else 
    echo "== read the file"
    while IFS= read -r filename
    do
	if [ "$filename" ];then
	    file_op $cmd $filename
	fi
    done < CMLIST.txt
fi

