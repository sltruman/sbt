#include <iostream>
#include <signal.h>
#include "TCPClient.h"

TCPClient tcp;

void sig_exit(int s)
{
	tcp.exit();
	exit(0);
}
// change ip and msg to test. msg must follow some rules
int main(int argc, char *argv[])
{
	signal(SIGINT, sig_exit);

	tcp.setup("127.0.0.1",9898);
	while(1)
	{
		char msg[] = "a 1 80 80\nx 1 200 200\nb 2 80 80";
		// char msg[] = "ResizePallet 33 33"; //change pallet to size: 33cm * 33cm
		// char msg[] = "ResetPallet";
		tcp.Send(msg);
		string rec = tcp.receive();
		cout<<"***** client recv:\n"<<rec<<endl;
		if( rec != "" )
		{
			cout << "Server Response:" << rec << endl;
		}else if (strcmp(rec.c_str(), msg) == 0)
		{
			cout <<"ok!!!"<<endl;
		}
		else 
		{
			cout<<"time out!"<<endl;
		}

		sleep(15);
	}
	return 0;
}
