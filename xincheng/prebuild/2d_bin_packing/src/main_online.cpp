#include "CPlanning_box_davit.h"
#include "CPlanning_box_davit.cpp"
#include "split.cpp"
// #include "server.cpp"
// #include "get_boxes.cpp"

// #include <iostream>
// using namespace std;

namespace OnlinePacking{ 

int xx = 10;
int yy = 30;

int min_box_size = 10;
bool is_test = true;
vector<GAPacking::boxinfo> place_box;
vector<GAPacking::boxinfo> placed_boxes;
GAPacking::CPlanning_Box PlanningBox(xx, yy,min_box_size);



int OnlinePlacement(bool save_results = false)
{

	
	int num_box_packed = 0;
	PlanningBox.Reset();

	bool have_box_placed = true;
	while (have_box_placed)
	{
		have_box_placed = false;
		
		for (int j = 0; j < place_box.size(); j++)
		{
			if (place_box[j].packst ==0)
			{
				cout <<"coming box number:\t"<<j<<endl;
				bool result_planning = PlanningBox.PlacementPlanning(place_box[j],save_results);
				int k = PlanningBox.UpdateState(place_box[j]);
				if (result_planning ==1)
				{
					cout<<"placement success"<<endl;
					have_box_placed = true;
					num_box_packed ++;
					placed_boxes.push_back(place_box[j]);
				}
				else
				{
					cout<<"placement failed"<<endl;
				}
			}
		}
		cout<<"current\t"<<num_box_packed<<"\tbox packed"<<endl;
		if(have_box_placed)
		{
			cout <<"pallet is full, clear pallet and start packing the rest boxes"<<endl;
			PlanningBox.Reset();
			GAPacking::boxinfo tmp_box;
			tmp_box.id = "0";
			placed_boxes.push_back(tmp_box);
		}
	}
	// for (int j = 0; j < place_box.size(); j++)
	// {
	// 	bool result_planning = PlanningBox.PlacementPlanning(place_box[j],save_results);
	// 	int k = PlanningBox.UpdateState(place_box[j]);
	// 	if (result_planning ==1)
	// 	{
	// 		num_box_packed ++;
	// 		placed_boxes.push_back(place_box[j]);
	// 	}
	// 	else 
	// 	{
	// 		cout <<"pallet is full, clear pallet and restart packing"<<endl;
	// 		PlanningBox.Reset();
	// 		GAPacking::boxinfo tmp_box;
	// 		tmp_box.id = "0";
	// 		placed_boxes.push_back(tmp_box);
	// 		j--;
	// 	}
	// }
	cout <<"placement end, placed\t"<<num_box_packed<<"\tboxes"<<endl;
	if (placed_boxes.size() <1)
	{
		cout<<"no box placed"<<endl;
		GAPacking::boxinfo tmp_box;
		tmp_box.id = "0";
		placed_boxes.push_back(tmp_box);
	}
	return num_box_packed;
}

int Encode(string &boxmessage)
{
	vector<string> strboxes = Split::split(boxmessage, "\n");
	for(vector<string>::size_type i = 0; i != strboxes.size(); ++i) 
	{
		vector<string> strbox = Split::split(strboxes[i], " ");
		GAPacking::boxinfo new_box;
		new_box.id = strbox[0];
		new_box.state = std::stoi(strbox[1]);
		new_box.dim1 = std::stoi(strbox[2]);
		new_box.dim2 = std::stoi(strbox[3]); 
		// new_box.packst = 0;
		cout <<i<<"\tnew coming box:\t"<<new_box.id <<"\t"<<new_box.state <<"\t"<<new_box.dim1<<"\t"<<new_box.dim2<<endl;
		// cout <<"new box extra information:\t"<<new_box.dim3<<"\tpackst:\t"<<new_box.packst<<endl;
		place_box.push_back(new_box);
	}

	return 1;
}
int Decode(string &placementmessage)
{
	placementmessage = "";
	for (int i = 0; i < placed_boxes.size(); i++)
	{
		string msg = "";
		msg += placed_boxes[i].id;
		msg += " ";
		msg += to_string(placed_boxes[i].posx);
		msg += " ";
		msg += to_string(placed_boxes[i].posy);
		msg += " ";
		msg += to_string(placed_boxes[i].posz);
		msg += " ";
		msg += to_string(placed_boxes[i].rotx);
		msg += " ";
		msg += to_string(placed_boxes[i].roty);
		msg += " ";
		msg += to_string(placed_boxes[i].rotz); 
		msg += "\n";

		cout << i <<"\t packed box:\t"<<msg<<endl;
		placementmessage += msg;
	}
	
	
	return 0;
}

int ResetPallet()
{
	PlanningBox.Reset();
	place_box.clear();
	placed_boxes.clear();
	cout<<"pallet reset end"<<endl;
	return 0;
}
int ResizePallet(int xx, int yy)
{
	PlanningBox.Setup(xx,yy);
	place_box.clear();
	placed_boxes.clear();
	cout<<"pallet has been resized to:\t"<<PlanningBox.pallet_x<<"\t"<<PlanningBox.pallet_y<<endl;
	return 0;
}

int CheckMSG(string &boxmessage, string &placementmessage)
{
	int spec_msg = 0;
	vector<string> msgs = Split::split(boxmessage, "\n");
	vector<string> msg = Split::split(msgs[0], " ");
	if(msg[0]=="ResizePallet")
	{
		int xx = std::stoi(msg[1]);
		int yy = std::stoi(msg[2]);
		ResizePallet(xx,yy);
		placementmessage = "PalletResize done.";
		spec_msg = 1;
	}
	else if(msg[0]=="ResetPallet")
	{
		ResetPallet();
		placementmessage = "PalletReset done.";
		spec_msg = 1;
	}
	return spec_msg;
}

int PlanPlacement(string &boxmessage, string &placementmessage)
{
	
	if (CheckMSG(boxmessage,placementmessage))
	{
		return 1;
	}
	place_box.clear();
	placed_boxes.clear();
	Encode(boxmessage);
	OnlinePlacement(is_test);
	Decode(placementmessage);

	return 0;
}

}